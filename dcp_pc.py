#decentralized_communication_protocol

#pip install
#subscribe 
from nacl.signing import SigningKey, VerifyKey
import nacl.exceptions#异常类型




import os
import sys
import hashlib
import socket
import struct
import sys
import threading
import time
import json
import subprocess
import secrets
import webbrowser

from urllib.parse import quote
from urllib.parse import unquote
from pathlib import Path

os.system('cls')

py_file_path = Path(__file__).resolve()
base_dir = py_file_path.parent.parent

argv = sys.argv
port_offset=0
if len(argv)>=2:
    port_offset=int(argv[1])

python_exe=base_dir/"software"/"py312"/"python.exe"
qbit_exe=base_dir/"software"/"qbittorrent_520.exe"

user_dir=base_dir/"user_data"/f"user_{port_offset}"
dcp_data_dir=user_dir/"dcp"
qbit_profile=user_dir/"qbit"
bt_down_dir =user_dir/"bt_down"

#config
udp_port =52014
http_port=16384
qbit_port= 8192
vps_ip='2001:19f0:1000:16bc:5400:06ff:fe29:acbc'
default_pubkey_hex = "ab30eba53685f719adfa0f77055b62f492d4750971aaa757e0d6ddce899edaea"
private_key_folder=dcp_data_dir/"subscribe"/"private_key_seed"
pub_sig_folder    =dcp_data_dir/"subscribe"/"pub_sig"

def get_file_names_single_level(dir_path: str) -> list[str]:
    """
    使用 pathlib 仅获取指定文件夹第一层的所有文件名（排除子文件夹名）
    """
    file_names = []
    try:
        path_obj = Path(dir_path)
        # 1. 确保路径存在且确实是一个目录
        if path_obj.exists() and path_obj.is_dir():
            # 2. 迭代当前目录下的所有子项
            for item in path_obj.iterdir():
                if item.is_file():
                    file_names.append(item.name)  # .name 获取纯文件名（如 "sig.bin"）
    except Exception as e:
        print(f"pathlib 读取文件夹失败: {e}")
        
    return file_names

def get_sha256(a:bytes)->bytes:
    hash = hashlib.sha256(a).digest()#32 bytes
    return hash
def get_k_channel_subscribe(pub_key_bytes:bytes)->bytes:
    k_channel_hash = get_sha256(pub_key_bytes+b'subscribe')
    return k_channel_hash

if 1:#global para
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)#ipv6 udp

    use_udp_port=udp_port+port_offset
    http_port+=port_offset
    qbit_port+=port_offset
    
    addr_storage=dict()
    msg_storage=dict()#目标是更新 msg[k],先更新addr_strage[k],再向他们索要 msg
    msg_list_local=list()#msg=[k,v]
    task_dict=dict()
    kt_channel=b"kt_channel"#记录所有ip的频道。此频道没有内容msg，不响应对此频道内容msg的请求
    
    front_end_dm=[0]
    private_key_seed_list=[b""]

HTML_PAGE = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nAccess-Control-Allow-Origin: *\r\n\r\n
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <title>decentralized_communication_protocol</title>
        </head>
        <body style="background:#1e1e24; color:#fff; font-family:sans-serif; padding:20px;">

            <!-- 博主端 -->
            <div style="border: 1px dashed #555; padding: 15px; margin-bottom: 20px;">
                <h3>【博主端】发布内容</h3>
                <input type="text" id="dir_path" placeholder="目录路径，如 D:/myfiles"
                    style="width:350px; padding:6px;">
                <button onclick="publishContent()"
                        style="padding:6px 12px; background:#007acc; color:#fff; border:none; cursor:pointer;">
                    做种并发布
                </button>
                <pre id="pub-box" style="margin-top:10px; background:#15151d; color:#0f0; padding:8px;"></pre>
            </div>

            <!-- 粉丝端 -->
            <div style="border: 1px dashed #555; padding: 15px;">
                <h3>【粉丝端】订阅更新</h3>
                <button onclick="syncAndVerify()"
                        style="padding:6px 12px; background:#444; color:#fff; border:none; cursor:pointer;">
                    查询更新
                </button>
                <pre id="display-box" style="margin-top:15px; padding:10px; background:#15151d; color:#ffc107;">
                    等待操作...
                </pre>
            </div>

            <script>
                function publishContent() {
                    const box = document.getElementById("pub-box");
                    const dirPath = document.getElementById("dir_path").value;
                    box.innerText = "正在建种并广播，请稍候...";
                    fetch("/api/publish_content", {
                        method: "POST",
                        headers: { "Content-Type": "text/plain" },
                        body: "dir=" + encodeURIComponent(dirPath)
                    })
                    .then(res => res.text())
                    .then(text => { box.innerText = text; });
                }

                function syncAndVerify() {
                    const box = document.getElementById("display-box");
                    box.innerText = "正在查询...";
                    fetch("/api/sub_sync", { method: "POST" })
                    .then(res => res.text())
                    .then(text => {
                        if (text.startsWith("updated")) box.style.color = "#0f0";
                        else if (text.startsWith("waiting")) box.style.color = "orange";
                        else box.style.color = "red";
                        box.innerText = text;
                    });
                }
            </script>
        </body>
    </html>
"""

def send_to_channel(k,rqm):
    sk=addr_storage[k]
    skl=list(sk)
    if skl:
        for i in range(len(skl)):
            that_addr = skl[i]
            try:
                print(f"send_to_channel{rqm}{that_addr}")
                sock.sendto(rqm,that_addr)
            except Exception as e:
                print(f"error@send_to_channel()sock.sendto->{e}")
                print(k,rqm)
def update_channel_k(type_k:int,x:int,c:int,k:bytes):
    #如何更新k频道的联系人
    #问你已知的所有人，k频道的联系人是哪些
    #即是kt频道本身，也是如此更新

    # if k not in addr_storage:
    #     addr_storage[k]=set()#init k
    # sk=addr_storage[k]

    xf=x

    x0=xf%256
    xf=xf//256
    x1=xf%256

    print(f"update_channel_k->task->[type_k,k]->{type_k}->{k}")
    task_dict[x]=[type_k,k]#0表示请求地址，2表示请求内容，k表示频道

    cf=c%256#数量

    ccl = [type_k,x0,x1,cf]#四字节，什么请求，什么回执标记，需要多少条
    bcc = bytes(ccl)

    rqm=bcc+k#k表示哪个频道
    
    if type_k==0:#request addr.注意，也可以向同频道的人请求这个频道的节点，这叫做pex，peer之间交换peer列表
        k0=kt_channel
    elif type_k==2:#request msg
        k0=k
    else:
        k0=kt_channel

    send_to_channel(k0,rqm)

#bittorrent
QBIT_HOST = "127.0.0.1"
def send_to_qbit(infohash_hex: str, save_path: str = "./downloads") -> str:
    try:
        magnet = f"magnet:?xt=urn:btih:{infohash_hex}"
        body = f"urls={magnet}&savepath={save_path}"
        
        # resp = _qbit_post("/api/v2/torrents/add", body)
        # print(f"[BT] qBit 返回: {resp}")  # ← 看这里返回什么

        request = (
            f"POST /api/v2/torrents/add HTTP/1.1\r\n"
            f"Host: localhost:{qbit_port}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: {len(body.encode())}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(("127.0.0.1", qbit_port))
        s.sendall(request.encode())
        
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
        s.close()
        
        if b"Ok." in response:
            return f"updated: 已交给 qBittorrent\ninfohash: {infohash_hex}"
        else:
            return f"error: qBit 返回异常 -> {response.split(b'\r\n\r\n',1)[-1]}"
    except ConnectionRefusedError:
        return "error: 无法连接 qBittorrent，请确认 Web UI 已开启"
    except Exception as e:
        return f"error: {e}"
def _qbit_post(path, body="", content_type="application/x-www-form-urlencoded"):
    req = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {QBIT_HOST}:{qbit_port}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body.encode())}\r\n"
        f"Connection: close\r\n\r\n"
        f"{body}"
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((QBIT_HOST, qbit_port))
    s.sendall(req.encode())
    resp = b""
    while True:
        chunk = s.recv(4096)
        if not chunk: break
        resp += chunk
    s.close()
    _, _, body_bytes = resp.partition(b"\r\n\r\n")
    return body_bytes
def _qbit_get(path):
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {QBIT_HOST}:{qbit_port}\r\n"
        f"Connection: close\r\n\r\n"
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((QBIT_HOST, qbit_port))
    s.sendall(req.encode())
    resp = b""
    while True:
        chunk = s.recv(4096)
        if not chunk: break
        resp += chunk
    s.close()
    _, _, body_bytes = resp.partition(b"\r\n\r\n")
    return body_bytes
def infohash_from_torrent_bytes(torrent_bytes: bytes) -> str:
    # 找到 "4:info" 后面 info 字典的起止位置
    info_start = torrent_bytes.index(b"4:info") + len(b"4:info")
    # 从 info_start 开始，用 bencode 解析器找到字典结束位置
    info_end = _bencode_end(torrent_bytes, info_start)
    info_bytes = torrent_bytes[info_start:info_end]
    return hashlib.sha1(info_bytes).hexdigest()
def _bencode_end(data: bytes, start: int) -> int:
    """返回从 start 开始的 bencode 对象结束位置（不含）"""
    c = chr(data[start])
    if c == 'd':  # 字典
        i = start + 1
        while data[i:i+1] != b'e':
            i = _bencode_end(data, i)  # key
            i = _bencode_end(data, i)  # value
        return i + 1
    elif c == 'l':  # 列表
        i = start + 1
        while data[i:i+1] != b'e':
            i = _bencode_end(data, i)
        return i + 1
    elif c == 'i':  # 整数
        return data.index(b'e', start + 1) + 1
    elif c.isdigit():  # 字符串
        colon = data.index(b':', start)
        length = int(data[start:colon])
        return colon + 1 + length
def business_create_and_seed(dir_path: str) -> str:
    """
    博主端：指定目录 -> qBit 建种并做种 -> 返回 infohash 供 DCP 广播
    """
    try:
        dir_path = dir_path.strip()

        # 1. 提交建种任务
        body = (
            f"sourcePath={quote(dir_path)}"
            f"&startSeeding=true"
            f"&format=v1"   # v1 兼容性最好，粉丝旧客户端也能下
        )
        resp = _qbit_post("/api/v2/torrentcreator/addTask", body)
        # task_id = resp.decode().strip()
        # print(f"task_id->{task_id}")
        task_id = json.loads(resp.decode())["taskID"]
        print(f"task_id->{task_id}")
        if not task_id:
            return "error: qBit 未返回 taskID"
        print(f"[BT] 建种任务已提交 taskID={task_id}")
        if 0:
            # 2. 稍等片刻让 qBit 完成计算（小文件1秒够，大文件要轮询）
            time.sleep(2)
            # 3. 直接取 torrent 文件
            torrent_bytes = _qbit_get(f"/api/v2/torrentcreator/torrentFile?taskID={task_id}")
            if not torrent_bytes or torrent_bytes[:1] != b'd':
                return "error: 取 torrent 文件失败，可能还没建完，稍后重试"
        else:
            # 2. 轮询等待完成（建种可能要几秒到几分钟，视文件大小）
            for _ in range(120*100):  # 最多等 2 分钟
                time.sleep(0.01)
                status_resp = _qbit_get(f"/api/v2/torrentcreator/status?taskID={task_id}")
                status_data = json.loads(status_resp.decode())[0]
                print(f"status_data->{status_data}")
                status = status_data.get("status", "")
                print(f"[BT] 建种状态: {status}")
                if status=="Finished":
                    break
                if status=="Failed":
                    return f"error: qBit 建种失败 -> {status_data}"
            else:
                return "error: 建种超时"
            # 3. 取回 .torrent 文件内容
            torrent_bytes=_qbit_get(f"/api/v2/torrentcreator/torrentFile?taskID={task_id}")
        infohash = infohash_from_torrent_bytes(torrent_bytes)
        print(f"[BT] infohash={infohash}")

        # 5. 清理任务（可选）
        _qbit_post(f"/api/v2/torrentcreator/deleteTask", f"taskID={task_id}")

        return f"success: {infohash}"

    except ConnectionRefusedError:
        return "error: 无法连接 qBittorrent，请确认 Web UI 已开启"
    except Exception as e:
        return f"error: {e}"

def business_blogger_publish(content_bytes:bytes,private_key_seed:bytes,type_byte:bytes) -> str:
    """
    博主端业务：对新公告内容进行数字签名，并触发全网 P2P 扩散通知
    """
    try:
        private_key_obj=SigningKey(private_key_seed)
        public_key_bytes=private_key_obj.verify_key.encode()
        seq=0
        # if private_key_seed_file_path.exists():#get seq
        if 1:
            k=get_k_channel_subscribe(public_key_bytes)
            
            old_signed_packet=b""
            if k in msg_storage:
                old_signed_packet=msg_storage.get(k)
            
            if old_signed_packet:
                verify_key = VerifyKey(public_key_bytes)
                try:
                    print("business_blogger_publish()verifing the old one...")
                    old_verified=verify_key.verify(old_signed_packet)
                except Exception:
                    pass#签名验证失败 seq=0
                else:
                    len_seq=8
                    old_seq=int.from_bytes(old_verified[:len_seq],'big')
                    seq=old_seq+1
        seq_bytes=seq.to_bytes(8,'big')
        raw_body = seq_bytes + type_byte + content_bytes#encode 8+1+...
        signed_packet=private_key_obj.sign(raw_body)
        
        if 1:#to network
            k=get_k_channel_subscribe(public_key_bytes)
            msg_storage[k]=signed_packet
        # print("debug to network")
        if 1:#to disk
            pubkey_hex=public_key_bytes.hex()
            pub_sig_file=pub_sig_folder/(pubkey_hex+".sig")
            pub_sig_file.parent.mkdir(parents=True, exist_ok=True)
            pub_sig_file.write_bytes(signed_packet)
        # print("debug to disk")
        
        if 1:
            pubkey_hex=public_key_bytes.hex()
            print("\n\n\n__________________")
            print(f"pubkey_hex->{pubkey_hex}")
            print("__________________\n\n\n")

        
        rq_addr_int=0#addr request
        update_channel_k(type_k=rq_addr_int,x=201, c=0,k=k)
    except Exception as e:
        s=f"error: 广播失败 -> {e}"
    else:
        s=f"success: 广播成功！\n[Seq]: {seq}\n[内容]: {content_bytes.decode('utf-8')}"
    print(s)
    return s
def verify_signed_v(signed_packet,channel_public_key):
    print(f"verify_signed_v")
    verify_key = VerifyKey(channel_public_key)
    parsed_msg=b""
    try:
        # 把消息和签名传进去验证，如果对不上会直接抛出异常
        print("verify_signed_v()verifing the new one...")
        verified_msg = verify_key.verify(signed_packet)
        # verify_key.verify(seq_msg,signature)
    except nacl.exceptions.BadSignatureError:
        print("verify fail")
    else:
        print("verify success")
        if 1: # seq, msg = parse(received_data)
            received_data = verified_msg
            len_seq=8  # 约定好的 8 字节长度
            parsed_seq = int.from_bytes(received_data[:len_seq],'big')
            type_byte_int = received_data[len_seq]
            parsed_type_byte=received_data[len_seq]
            parsed_msg = received_data[len_seq+1:]
            if 1:# 从内存kv读旧数据，解析旧seq
                k=get_k_channel_subscribe(channel_public_key)
                old_signed_packet=b""
                if k in msg_storage:
                    old_signed_packet = msg_storage.get(k)
                old_seq=-1
                if old_signed_packet:
                    try:
                        print("verify_signed_v()verifing the old one...")
                        old_verified=verify_key.verify(old_signed_packet)
                    except Exception:
                        pass#内存里存的是异常签名
                    else:
                        old_seq=int.from_bytes(old_verified[:len_seq],'big')
                print(f"old_seq->{old_seq}")
            print(f"len(received_data)->{len(received_data)}")
            print(f"parsed_seq->{parsed_seq}")
            print(f"old_seq->{old_seq}")
            print(f"parsed_seq>old_seq->{parsed_seq>old_seq}")
            if parsed_seq>old_seq:
                #最新消息
                msg_storage[k]=signed_packet#更新内存中的签名
                if 1:
                    pubkey_hex=channel_public_key.hex()
                    pub_sig_file=pub_sig_folder/(pubkey_hex+".sig")
                    pub_sig_file.parent.mkdir(parents=True, exist_ok=True)
                    pub_sig_file.write_bytes(signed_packet)


                # print(f"解析出来的 seq 序号: {parsed_seq}")
                # print(f"newest msg->{parsed_msg.decode('utf-8')}")
                print(f"parsed_type_byte->{parsed_type_byte}")
                print(f"newest msg->{parsed_msg}")
                if type_byte_int == 1:  # bt
                    infohash_hex=parsed_msg.decode('utf-8').strip()
                    send_to_qbit(infohash_hex,bt_down_dir)
                    print(f"new bt.send_to_qbit({infohash_hex})")
            else:
                print(f"not new msg")
    return parsed_msg
def business_sub_sync(pub_key_bytes: bytes) -> str:#like subscribe demo front_end
    try:
        print(f"business_sub_sync()")
        k=get_k_channel_subscribe(pub_key_bytes)


        front_end_dm[0]=0
        update_channel_k(0,0,0,k)#rq_type=0 x=301
        for _ in range(1024):
            # print(f"business_sub_sync()front_end_dm[0]->{front_end_dm[0]}")
            time.sleep(0.01)
            if(front_end_dm[0]<=0):
                pass
            else:
                break

        front_end_dm[0]=1
        update_channel_k(2,1,0,k)
        for _ in range(1024):
            # print(f"business_sub_sync()front_end_dm[0]->{front_end_dm[0]}")
            time.sleep(0.01)
            if(front_end_dm[0]<=1):
                pass
            else:
                break

        if not msg_list_local:
            return "error: 未收到频道消息"


        msg=msg_list_local[-1]#[k,v]
        signed_packet=msg[1]
        # signed_packet=signed_packet_1[0]
        if 1:
            print("验证签名")
            verified_msg=verify_signed_v(signed_packet,pub_key_bytes)
            print(f"verified_msg->{verified_msg}")
        return verified_msg
    except Exception as e:
        s=f"error: 触发失败 -> {e}"
        print(s)
        return s

def handle_http_protocol(client_sock):
    """
    解析原生 HTTP 协议层
    """
    try:
        request_data = client_sock.recv(4096).decode('utf-8', errors='ignore')
        if not request_data: return
        lines = request_data.split("\r\n")
        first_line = lines[0].split(" ")
        if len(first_line) < 2: return
        method, path = first_line[0], first_line[1]
        
        private_key_seed=private_key_seed_list[0]
        if method == "GET" and path == "/":
            client_sock.sendall(HTML_PAGE.encode('utf-8'))
            return
        elif method == "POST" and path == "/api/blog_pub":# 在 handle_http_protocol 函数的路由判断里，加上这个发送分支：
            body_str = lines[-1].strip()
            # 约定前端发来的格式为: seq=101&content=Hello World
            if "seq=" in body_str and "content=" in body_str:
                part1 = body_str.split("&content=")
                seq_text = part1[0].split("seq=")[1]
                content_text = part1[1]
                content_bytes=content_text.encode('utf-8')
                
                type_byte_int=int(seq_text)
                # type_byte_int=0#text
                # type_byte_int=1#bt
                # type_byte_int=2#http
                # type_byte_int=3#ipfs
                type_byte=int(type_byte_int).to_bytes(1,'big')
                response_text = business_blogger_publish(content_bytes,private_key_seed,type_byte)
            else:
                response_text = "error: missing seq or content"
            # 标准纯文本 HTTP 回应
            http_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(response_text.encode('utf-8'))}\r\n"
                "\r\n"
                f"{response_text}"
            )
            client_sock.sendall(http_response.encode('utf-8'))
            return
        elif method == "POST" and path == "/api/publish_content":
            body_str = lines[-1].strip()
            if "dir=" in body_str:
                dir_path = unquote(body_str.split("dir=")[1])
                
                # 1. 建种+做种
                result = business_create_and_seed(dir_path)
                print(f"建种+做种->{result}")
                if result.startswith("success:"):
                    infohash = result.replace("success: ", "").strip()
                    content_bytes=infohash.encode("utf-8")
                    # type_byte_int=0#text
                    type_byte_int=1#bt
                    # type_byte_int=2#http
                    # type_byte_int=3#ipfs
                    type_byte=int(type_byte_int).to_bytes(1,'big')
                    response_text = business_blogger_publish(content_bytes,private_key_seed,type_byte)
                else:
                    response_text = result
            else:
                response_text = "error: missing dir"
            
            # 组装 HTTP 响应...
            # 组装纯文本 HTTP 回应
            http_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(response_text)}\r\n"
                "\r\n"
                f"{response_text}"
            )
            client_sock.sendall(http_response.encode('utf-8'))
        elif method == "POST" and path == "/api/sub_sync":
            if 1:
                file_name_list=get_file_names_single_level(pub_sig_folder)
                results = []
                for i in range(len(file_name_list)):
                    file_name=file_name_list[i]
                    pubkey_hex=file_name.split(".")[0]
                    try:
                        pub_key_bytes = bytes.fromhex(pubkey_hex)
                        verified_msg = business_sub_sync(pub_key_bytes)
                        

                        if isinstance(verified_msg, bytes):
                            text = verified_msg.decode('utf-8', errors='ignore')
                        else:
                            text = str(verified_msg)

                        results.append(f"频道 {pubkey_hex[:16]}...\n{text}")
                        # if verified_msg:
                        #     results.append(f"频道 {pubkey_hex[:16]}...\n{verified_msg.decode('utf-8')}")
                    except Exception as e:
                        results.append(f"error: {pubkey_hex[:16]}... -> {e}")
                response_text = "\n\n".join(results) if results else "暂无订阅频道"

            # 组装纯文本 HTTP 回应
            http_response=(
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(response_text)}\r\n"
                "\r\n"
                f"{response_text}"
            )
            client_sock.sendall(http_response.encode('utf-8'))
        else:
            # 404 纯文本返回
            client_sock.sendall("HTTP/1.1 404 Not Found\r\n\r\nerror: 404".encode())
    except Exception as e:
        print(f"[HTTP Socket Error] {e}")
    finally:
        client_sock.close()
def thread_tcp_server():
    server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("::",http_port))
    server_sock.listen(10)
    ss=f'http://localhost:{http_port}/'
    print(ss)
    webbrowser.open(ss)
    while True:
        try:
            client_sock, _ = server_sock.accept()
            # 收到 TCP 连接，丢给协议层处理，采用守护线程防止阻塞主循环
            threading.Thread(target=handle_http_protocol, args=(client_sock,), daemon=True).start()
        except Exception as e:
            print(f"[TCP Server Main Loop Error] {e}")
def thread_udp_server():
    if 1:#ipv6 udp
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.bind(("::",use_udp_port))
    if 1:#init kt_channel
        addr_storage[kt_channel]=set()
        skt=addr_storage[kt_channel]
        that_ip="::1"#local loop or vps ip
        that_ip=vps_ip
        addr_0_recevie=(that_ip,udp_port)
        skt.add(addr_0_recevie)
    while True:#server loop
        try:
            data,client_addr=sock.recvfrom(4096)
            print(f"{data}{client_addr}")
            rq_addr_int=0#addr request
            rs_int=1#response
            rq_msg_int=2#msg request
            if data:
                head = data[0]
                print(f"{head==0}")
                if head==rq_addr_int:#receive address request
                    print("receive address request")
                    x0=data[1]
                    x1=data[2]
                    c=data[3]
                    bcc=[rs_int,x0,x1]
                    rsm=b""
                    rsm+=bytes(bcc)
                    c1=2**c#need send how many response
                    if 1:
                        c1=1#以后再改为发送多条响应
                    k = data[4:]
                    if k not in addr_storage:
                        addr_storage[k] = set()#init k
                    sk = addr_storage[k]
                    if 1:#get_peers
                        for i in range(32):
                            if i>=len(sk):
                                break
                            skl = list(sk)
                            p = skl[i]
                            if p!=client_addr:#要不要先enocde再比较
                                if 1:#ip encode
                                    ip_bin = socket.inet_pton(socket.AF_INET6, p[0])
                                    port_bin = struct.pack('!H', p[1])
                                    addr_bin = ip_bin + port_bin
                                rsm+=addr_bin
                    sk.add(client_addr)#add
                    skt=addr_storage[kt_channel]#无论来访者请求哪个频道，都把来访者加到kt频道
                    skt.add(client_addr)#add
                    print(f"addr_storage->{addr_storage}")
                    if 0:
                        print(f"k->{k}")
                        print(f"rsm->{rsm}")


                        sk = addr_storage[k]

                        print(f"sk->{sk}")
                        
                        print(f"skl->{list(sk)}")
                    sock.sendto(rsm,client_addr)
                elif head==rs_int:#receive response
                    print("\n\n\n")
                    print("receive response")
                    x0=data[1]
                    x1=data[2]
                    x=x0+x1*256#查是哪个任务，看看是回复给什么请求的响应 x类似于端口
                    
                    if 1:
                        task=task_dict[x]
                        print(f"x->{x}")
                        print(f"{task_dict}")
                        print(f"{x in task_dict}")
                        print(f"{task_dict[x]}")
                        print("___\n\n")
                    if task:
                        rq1=task[0]
                        k1=task[1]
                        print(f"rq1 k1{rq1}->{k1}")
                        if rq1==rq_addr_int:
                            # print("debug 我们刚刚发给对方的是地址请求")
                            # print(f"debug len(data)->{len(data)}")
                            addr_list = list()
                            if 1:
                                ipv6_len=16
                                port_len=2
                                addr_len=ipv6_len+port_len
                                xd=3#响应报文的前缀是3字节 1,x x占两字节
                                while True:
                                    # print("w t")
                                    if len(data)-xd<addr_len:
                                        break
                                    ip_bin = data[xd:xd+ipv6_len]
                                    port_bin = data[xd+ipv6_len:xd+addr_len]
                                    xd+=addr_len
                                    ip_str=socket.inet_ntop(socket.AF_INET6,ip_bin)
                                    port_int=struct.unpack('!H',port_bin)[0]
                                    addr=(ip_str,port_int)
                                    addr_list.append(addr)
                            if 1:#add addr
                                # print("debug add")
                                # print(f"{len(addr_list)}")
                                # print(f"{addr_storage}")
                                
                                if k1 not in addr_storage:
                                    addr_storage[k1]=set()
                                sk=addr_storage[k1]
                                for i in range(len(addr_list)):
                                    # print("debug add in..")
                                    addr=addr_list[i]
                                    sk.add(addr)

                                if port_offset==2:
                                    front_end_dm[0]=1
                                    
                                if port_offset==4:
                                    front_end_dm[0]=1


                                # print("debug add end")
                                print(f"front_end_dm[0]->{front_end_dm[0]}")
                            if 0:#print
                                for addr in addr_list:
                                    print(addr)
                        elif rq1==rq_msg_int:
                            
                            if port_offset==2:
                                front_end_dm[0]=2
                                print("通知前端消息收到了")

                            v1=data[4:]
                            # if port_offset==4:
                            #     print('4进程收到了签名')
                            #     signed_packet_1[0]=v1
                            print(f"我们收到了对内容请求的响应k->{k1}->v->{v1}")
                            msg_list_local.append([k1,v1])
                elif head==rq_msg_int:#receive msg request
                    print("receive msg request")
                    # print(f"data->{data}->")
                    # print(f"msg_storage->{msg_storage}")
                    k=data[4:]

                    rsm=b""
                    if msg_storage[k]:#若没有就不回复了。内容请求本就不必回复，addr请求需要回复，尤其是kt_channel。
                        x0=data[1]
                        x1=data[2]
                        c=0%256
                        # rs=bytes([1])#表示响应
                        bcc=[rs_int,x0,x1,c]
                        rsm+=bytes(bcc)
                        rsm+=msg_storage[k]
                    sock.sendto(rsm,client_addr)
                # print("debug try end")
        except Exception as e:
            # pass
            print(f"error@thread_udp_server()->{e}")

def prepare_qbit_config():
    config_dir = qbit_profile / "qBittorrent" / "config"
    ini_path = config_dir / "qBittorrent.ini"

    if not ini_path.exists():

        ini_content_list = []

        # Preferences
        ini_content_list.append("[Preferences]")
        ini_content_list.append("WebUI\\Enabled=true")
        ini_content_list.append(f"WebUI\\Port={qbit_port}")
        ini_content_list.append("WebUI\\LocalHostAuth=false")

        # 用户名密码必须在 Preferences 下
        ini_content_list.append("WebUI\\Username=admin")
        ini_content_list.append(
            'WebUI\\Password_PBKDF2="@ByteArray(qonqo/id7jqCvPk3QmEQAA==:OHDI+GMZPCkc67wMNXEHCv5OpI2uCX6Vz47swhHjJgAveuj6kVMQK9hbtIa7NDZLZcKUcVg49yqNZZmxuJgSgg==)"'
        )

        ini_content_list.append("")

        # Application
        ini_content_list.append("[Application]")
        ini_content_list.append("FileLogger\\Enabled=false")
        ini_content_list.append("")

        # LegalNotice
        ini_content_list.append("[LegalNotice]")
        ini_content_list.append("Accepted=true")
        ini_content_list.append("")

        # BitTorrent
        ini_content_list.append("[BitTorrent]")
        ini_content_list.append("Session\\StartPaused=false")
        ini_content_list.append("Session\\QueueingSystemEnabled=false")
        ini_content_list.append("")

        # Meta
        ini_content_list.append("[Meta]")
        ini_content_list.append("MigrationVersion=8")

        ini_content = "\n".join(ini_content_list)

        config_dir.mkdir(parents=True, exist_ok=True)
        ini_path.write_text(ini_content, encoding="utf-8")
def prepare_private_key_seed():
    private_key_folder.mkdir(parents=True, exist_ok=True)
    if not any(private_key_folder.iterdir()):#如果一个seed也没有
        private_key_seed=secrets.token_bytes(32)
        private_key_obj=SigningKey(private_key_seed)
        public_key_bytes=private_key_obj.verify_key.encode()
        public_key_hex=public_key_bytes.hex()
        private_key_seed_file_path=private_key_folder / f"{public_key_hex}.seed"
        private_key_seed_file_path.write_bytes(private_key_seed)
def prepare_subscribe_sig():
    pub_sig_folder.mkdir(parents=True, exist_ok=True)
    if not any(pub_sig_folder.iterdir()):#如果一个订阅也没有
        sig_file=pub_sig_folder/f"{default_pubkey_hex}.sig"#文件存在就会订阅
        sig_file.write_bytes(b"")
def init_dcp():
    prepare_qbit_config()
    prepare_private_key_seed()
    prepare_subscribe_sig()

def load_file():#订阅频道 读外存
    if 1:#read private key
        file_name_list=get_file_names_single_level(private_key_folder)
        file_name=file_name_list[0]
        pubkey_hex=file_name.split(".")[0]
        file_path=private_key_folder/file_name
        private_key_seed=file_path.read_bytes()
        private_key_seed_list[0]=private_key_seed
    if 1:#read public key
        #把 pub_sig 都读到内存中 msg_storage
        file_name_list=get_file_names_single_level(pub_sig_folder)
        for i in range(len(file_name_list)):
            file_name=file_name_list[i]    
            pubkey_hex=file_name.split(".")[0]
            pubkey=bytes.fromhex(pubkey_hex)
            k=get_k_channel_subscribe(pubkey)
            file_path=pub_sig_folder/file_name
            if file_path.exists():
                pub_sig=file_path.read_bytes()
                msg_storage[k]=pub_sig
def main():
    init_dcp()
    load_file()
    if 1:#qbit
        subprocess.Popen([str(qbit_exe), f"--profile={str(qbit_profile)}"])
    thread_list=list()
    t=threading.Thread(target=thread_udp_server,daemon=True);thread_list.append(t)
    t=threading.Thread(target=thread_tcp_server,daemon=True);thread_list.append(t)
    for i in range(len(thread_list)):
        t=thread_list[i]
        t.start()
    for i in range(len(thread_list)):
        t=thread_list[i]
        t.join()
if __name__ == "__main__":
    main()