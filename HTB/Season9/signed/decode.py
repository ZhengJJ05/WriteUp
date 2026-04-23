import struct

def binary_sid_to_string(hex_sid):
    # 直接处理你的十六进制SID，无需额外配置
    binary_sid = bytes.fromhex(hex_sid)
    version = binary_sid[0]
    sub_auth_count = binary_sid[1]
    authority = struct.unpack(">Q", b"\x00\x00" + binary_sid[2:8])[0]
    sid_parts = [f"S-{version}", str(authority)]
    offset = 8
    for _ in range(sub_auth_count):
        sub_auth = struct.unpack("<I", binary_sid[offset:offset+4])[0]
        sid_parts.append(str(sub_auth))
        offset += 4
    return "-".join(sid_parts)

# 你的十六进制SID（已直接填入）
your_hex_sid = "0105000000000005150000005b7bb0f398aa2245ad4a1ca451040000"
try:
    result = binary_sid_to_string(your_hex_sid)
    print(f"转换成功！标准SID：{result}")
except Exception as e:
    print(f"错误：{e}")
