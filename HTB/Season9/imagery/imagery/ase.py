import pyAesCrypt

GREEN = "\033[92m"   # 亮绿色
RESET = "\033[0m"    # 恢复默认颜色


def decrypt(password,AESfile,output):
    try:
        res = pyAesCrypt.decryptFile(AESfile, output, str(password))
        if not res:
            return True
    except:
        return False
            
with open('/root/Desktop/wordlists/test.txt', 'rb') as f:  # change it!
    passwords = [line.decode('latin1').strip() for line in f]
    for password in passwords:
        res = decrypt(password,"backup.zip.aes","backup.zip") # change it!
        if res:
            print(f"{GREEN}[+]{password}{RESET}")
            break
        else:
            print(f"[-]{password}")
