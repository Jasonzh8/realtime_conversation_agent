import socket
import random
import uuid
import hashlib
import re
import os
from dotenv import load_dotenv
load_dotenv()

# SIP 用户配置
SIP_USERNAME = os.getenv("SIP_USERNAME")
SIP_PASSWORD = os.getenv("SIP_PASSWORD")
SIP_PORT = 6070
SIP_SERVER = "119.8.185.241"
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = random.randint(20000, 40000)  # 本地随机端口

# 生成 REGISTER 请求
def build_register(username, server, local_ip, local_port, call_id, cseq, branch, auth_header=None):
    message = (
        f"REGISTER sip:{server} SIP/2.0\r\n"
        f"Via: SIP/2.0/TCP {local_ip}:{local_port};branch={branch};rport\r\n"
        f"Max-Forwards: 70\r\n"
        f"To: <sip:{username}@{server}>\r\n"
        f"From: <sip:{username}@{server}>;tag=123456\r\n"
        f"Call-ID: {call_id}@{local_ip}\r\n"
        f"CSeq: {cseq} REGISTER\r\n"
        f"Contact: <sip:{username}@{local_ip}:{local_port}>\r\n"
        f"Expires: 3600\r\n"
    )
    if auth_header:
        message += f"{auth_header}\r\n"
    message += "Content-Length: 0\r\n\r\n"
    return message

# 解析 401 中的 nonce 和 realm
def parse_authenticate_header(response, header_type="WWW-Authenticate"):
    response_text = response.decode(errors="ignore")
    # 查找指定类型的认证头
    auth_match = re.search(f'{header_type}: Digest (.*?)(?:\r\n|$)', response_text, re.IGNORECASE)
    if not auth_match:
        return None, None
    
    auth_content = auth_match.group(1)
    match_realm = re.search(r'realm="([^"]+)"', auth_content)
    match_nonce = re.search(r'nonce="([^"]+)"', auth_content)
    
    if match_realm and match_nonce:
        return match_realm.group(1), match_nonce.group(1)
    return None, None

# 生成 Authorization 头
def generate_authorization(username, password, realm, nonce, uri, method="REGISTER", auth_type="Authorization"):
    ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
    response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

    auth_header = (
        f'{auth_type}: Digest '
        f'username="{username}", '
        f'realm="{realm}", '
        f'nonce="{nonce}", '
        f'uri="{uri}", '
        f'response="{response}", '
        'algorithm=MD5'
    )
    return auth_header

# 发送并接收响应
def send_and_receive(sock, msg, server_addr=None):
    # TCP下直接send，不需要server_addr
    sock.send(msg.encode())
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            # SIP消息以\r\n\r\n结尾，收到完整消息就返回
            if b"\r\n\r\n" in data:
                break
        return data if data else None
    except socket.timeout:
        return None

# 主函数
def sip_register_with_auth(sock, call_id, cseq, branch):
    """使用提供的 socket 进行注册"""
    uri = f"sip:{SIP_SERVER}"
    print("📡 Step 1: Sending REGISTER (without authentication)")
    msg1 = build_register(SIP_USERNAME, SIP_SERVER, LOCAL_IP, LOCAL_PORT, call_id, cseq, branch)
    response1 = send_and_receive(sock, msg1, (SIP_SERVER, SIP_PORT))

    if not response1:
        print("❌ No response received for REGISTER")
        return None, None

    print("📥 Received REGISTER response:")
    print(response1.decode(errors="ignore"))

    if b"401 Unauthorized" not in response1:
        print("❌ 401 Unauthorized not received, abnormal process")
        return None, None

    realm, nonce = parse_authenticate_header(response1)
    if not realm or not nonce:
        print("❌ Failed to parse realm and nonce")
        return None, None

    print(f"🔐 Got realm: {realm}, nonce: {nonce}")

    auth = generate_authorization(SIP_USERNAME, SIP_PASSWORD, realm, nonce, uri)
    cseq += 1
    branch = f"z9hG4bK{random.randint(100000, 999999)}"

    print("Step 2: Sending REGISTER (with authentication)")
    msg2 = build_register(SIP_USERNAME, SIP_SERVER, LOCAL_IP, LOCAL_PORT, call_id, cseq, branch, auth_header=auth)
    response2 = send_and_receive(sock, msg2, (SIP_SERVER, SIP_PORT))

    if not response2:
        print("❌ No response received for authenticated REGISTER")
        return None, None

    print("📥 Received authenticated REGISTER response:")
    print(response2.decode(errors="ignore"))

    if b"200 OK" in response2:
        print("✅ Registration successful!")
        return realm, nonce
    elif b"403 Forbidden" in response2:
        print("❌ Registration failed: wrong password or account forbidden")
        return None, None
    else:
        print("⚠️ Registration response unclear, further check may be needed")
        return None, None

# 构造 ACK 请求
def build_ack(request_uri, from_header, to_header, call_id, cseq, branch, local_ip, local_port):
    message = (
        f"ACK {request_uri} SIP/2.0\r\n"
        f"Via: SIP/2.0/TCP {local_ip}:{local_port};branch={branch};rport\r\n"
        f"Max-Forwards: 70\r\n"
        f"To: {to_header}\r\n"
        f"From: {from_header}\r\n"
        f"Call-ID: {call_id}\r\n"
        f"CSeq: {cseq} ACK\r\n"
        "Content-Length: 0\r\n\r\n"
    )
    return message

# 构造 INVITE 请求
def build_invite(username, server, local_ip, local_port, call_id, cseq, branch, to_number, from_tag, auth_header=None):
    uri = f"sip:{to_number}@{server}"
    from_uri = f"sip:{username}@{server}"
    to_uri = f"sip:{to_number}@{server}"
    sdp = (
        "v=0\r\n"
        f"o=- 0 0 IN IP4 {local_ip}\r\n"
        f"s=VoIP Call\r\n"
        f"c=IN IP4 {local_ip}\r\n"
        "t=0 0\r\n"
        "m=audio 40000 RTP/AVP 0 101\r\n"
        "a=rtpmap:0 PCMU/8000\r\n"
        "a=rtpmap:101 telephone-event/8000\r\n"
        "a=fmtp:101 0-15\r\n"
    )
    message = (
        f"INVITE {uri} SIP/2.0\r\n"
        f"Via: SIP/2.0/TCP {local_ip}:{local_port};branch={branch};rport\r\n"
        f"Max-Forwards: 70\r\n"
        f"To: <{to_uri}>\r\n"
        f"From: <{from_uri}>;tag={from_tag}\r\n"
        f"Call-ID: {call_id}\r\n"
        f"CSeq: {cseq} INVITE\r\n"
        f"Contact: <sip:{username}@{local_ip}:{local_port}>\r\n"
        f"P-Preferred-Identity: <sip:{username}@{server}>\r\n"
        f"P-Asserted-Identity: <sip:{username}@{server}>\r\n"
        f"Content-Type: application/sdp\r\n"
        f"Content-Length: {len(sdp)}\r\n"
    )
    if auth_header:
        message += f"{auth_header}\r\n"
    message += "\r\n" + sdp
    return message

# 呼叫流程
def sip_call(sock, realm, nonce, call_id, to_number):
    """使用提供的 socket 和认证信息发起呼叫"""
    print(f"📞 Initiating call to {to_number}")
    uri = f"sip:{to_number}@{SIP_SERVER}"
    cseq_invite = 3
    branch_invite = f"z9hG4bK{random.randint(100000, 999999)}"
    from_tag = f"tag{random.randint(100000, 999999)}"  # 生成一个固定的from tag

    # 第一次 INVITE（不带认证）
    print("📡 Sending initial INVITE")
    invite_msg = build_invite(SIP_USERNAME, SIP_SERVER, LOCAL_IP, LOCAL_PORT, call_id, cseq_invite, branch_invite, to_number, from_tag)
    
    response_invite = send_and_receive(sock, invite_msg, (SIP_SERVER, SIP_PORT))

    if not response_invite:
        print("❌ No response received for initial INVITE")
        return

    print("📥 Initial INVITE response:")
    print(response_invite.decode(errors="ignore"))

    # 处理初始响应 - 处理100 Trying
    while b"100 Trying" in response_invite:
        print("⏳ Calling in progress (100 Trying)")
        # 100 Trying 后面会有其他响应，继续接收
        try:
            response_invite = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_invite += chunk
                if b"\r\n\r\n" in response_invite:
                    break
            print("\n📥 Received new response:")
            print(response_invite.decode(errors="ignore"))
        except socket.timeout:
            print("⌛️ Waiting for response timed out")
            return

    # 循环接收后续响应
    current_response = response_invite
    cancel_sent = False
    initial_response_handled = False
    
    for _ in range(10):  # 增加循环次数
        if not current_response:
            break

        response_text = current_response.decode(errors="ignore")
        
        if "180 Ringing" in response_text:
            print("🔔 Remote party is ringing (180 Ringing)")
        elif "183 Session Progress" in response_text:
            print("📞 Received 183 Session Progress - call is in progress...")
            # 不要自动取消，让呼叫继续
        elif "200 OK" in response_text and "CANCEL" in response_text:
            print("✅ CANCEL confirmed (200 OK for CANCEL)")
        elif "200 OK" in response_text and "INVITE" in response_text:
            print("✅ Call successful, remote party answered (200 OK)")
            # 这里应该发送 ACK 来确认 200 OK
            # 解析 To 头获取 tag
            to_match = re.search(r'^To: (.*)$', response_text, re.MULTILINE)
            if to_match:
                to_header_final = to_match.group(1).strip()
                ack_200_msg = build_ack(uri, f"<sip:{SIP_USERNAME}@{SIP_SERVER}>;tag={from_tag}", 
                                       to_header_final, call_id, cseq_invite, branch_invite, 
                                       LOCAL_IP, LOCAL_PORT)
                sock.send(ack_200_msg.encode())
                print("✉️ Sent ACK to confirm 200 OK")
            break
        elif "486 Busy" in response_text:
            print("🚫 Remote party is busy (486 Busy Here)")
            break
        elif "407 Proxy Authentication Required" in response_text and not initial_response_handled:
            print("🔐 Received 407 Proxy Authentication Required, preparing to re-authenticate and call")
            initial_response_handled = True

            # 从 407 响应中解析新的 realm 和 nonce
            proxy_realm, proxy_nonce = parse_authenticate_header(current_response, "Proxy-Authenticate")
            if not proxy_realm or not proxy_nonce:
                print("❌ Failed to parse realm and nonce from 407 response")
                break
            
            print(f"🔑 Got proxy authentication info - realm: {proxy_realm}, nonce: {proxy_nonce}")

            # 获取完整的 To 和 From 头，用于 ACK
            to_header_match = re.search(r'^To: (.*)$', response_text, re.MULTILINE)
            from_header_match = re.search(r'^From: (.*)$', response_text, re.MULTILINE)
            
            if not to_header_match or not from_header_match:
                print("❌ Failed to parse To/From header for ACK")
                break
            
            to_header = to_header_match.group(1).strip()
            from_header = from_header_match.group(1).strip()

            # 发送 ACK 确认收到 407
            ack_msg = build_ack(uri, from_header, to_header, call_id, cseq_invite, branch_invite, LOCAL_IP, LOCAL_PORT)
            sock.send(ack_msg.encode())
            print("✉️ Sent ACK to confirm 407 response")

            # 准备重新发送 INVITE
            cseq_invite += 1  # CSeq 必须递增
            branch_invite = f"z9hG4bK{random.randint(100000, 999999)}"  # 新的 branch

            # 使用代理认证信息生成 Proxy-Authorization 头
            proxy_auth = generate_authorization(
                SIP_USERNAME, 
                SIP_PASSWORD, 
                proxy_realm,  # 使用从407响应中获取的realm
                proxy_nonce,  # 使用从407响应中获取的nonce
                uri, 
                method="INVITE",
                auth_type="Proxy-Authorization"
            )

            # 重新发送带代理认证的 INVITE
            print("📡 Resending INVITE with proxy authentication")
            invite_msg_2 = build_invite(
                SIP_USERNAME, 
                SIP_SERVER, 
                LOCAL_IP, 
                LOCAL_PORT, 
                call_id, 
                cseq_invite, 
                branch_invite, 
                to_number, 
                from_tag,  # 使用相同的 from tag
                auth_header=proxy_auth
            )
            
            sock.send(invite_msg_2.encode())
            
            # 等待新的响应
            try:
                current_response, addr = sock.recvfrom(4096)
                print("\n📥 Received response after authentication:")
                print(current_response.decode(errors="ignore"))
                continue  # 继续处理循环
            except socket.timeout:
                print("⌛️ Waiting for authentication response timed out")
                break
        elif "403 Forbidden" in response_text or "401 Unauthorized" in response_text:
            print("❌ Call authentication failed (401/403)")
            break
        elif "404 Not Found" in response_text:
            print("❓ Remote number does not exist (404 Not Found)")
            break
        elif "487 Request Terminated" in response_text:
            print("🛑 Received 487 Request Terminated, sending ACK automatically")
            # 获取完整的 To 头
            to_match = re.search(r'^To: (.*)$', response_text, re.MULTILINE)
            if to_match:
                to_header_487 = to_match.group(1).strip()
                ack_msg_487 = build_ack(uri, f"<sip:{SIP_USERNAME}@{SIP_SERVER}>;tag={from_tag}", 
                                       to_header_487, call_id, cseq_invite, branch_invite, 
                                       LOCAL_IP, LOCAL_PORT)
                sock.send(ack_msg_487.encode())
                print("✉️ Sent 487 ACK")
            break
        
        # 接收下一个响应
        try:
            sock.settimeout(3)  # 减少等待时间
            current_response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                current_response += chunk
                if b"\r\n\r\n" in current_response:
                    break
            print("\n📥 Received new response:")
            print(current_response.decode(errors="ignore"))
        except socket.timeout:
            print("⌛️ Waiting for response timed out")
            break

# 运行
if __name__ == "__main__":
    import sys
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # 5秒超时
    sock.connect((SIP_SERVER, SIP_PORT))

    call_id = str(uuid.uuid4()).replace('-', '')[:16]  # 使用更长的 call-id
    branch = f"z9hG4bK{random.randint(100000, 999999)}"
    cseq = random.randint(100, 999)

    # 从命令行参数获取呼叫号码
    if len(sys.argv) > 1:
        to_number = sys.argv[1]
    else:
        print("❌ No destination number specified, please provide it as a command line argument.")
        sys.exit(1)

    try:
        # 1. 注册
        realm, nonce = sip_register_with_auth(sock, call_id, cseq, branch)

        # 2. 如果注册成功，则发起呼叫
        if realm and nonce:
            # 等待一小段时间，确保服务器处理完注册
            import time
            time.sleep(1)
            
            sip_call(sock, realm, nonce, call_id, to_number)
        else:
            print("❌ Cannot proceed with call because registration failed.")

    finally:
        print("🔚 Process finished, closing socket.")
        sock.close()
