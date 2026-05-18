import socket
import struct
import sys
import threading
import time


import os
os.system('cls')
# def build_response():
# sys.cmd("cls")


if 1:#global para
    #config
    this_port = 17700

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    argv = sys.argv
    port_offset=0
    if len(argv)>=2:
        port_offset=int(argv[1])


    addr_storage=dict()
    msg_storage=dict()#目标是更新 msg[k],先更新addr_strage[k],再向他们索要 msg
    task_dict=dict()
    kt_channel=b"kt_channel"#记录所有ip的频道。此频道没有内容msg，不响应对此频道内容msg的请求
    
    front_end_dm=[0]


def send_to_channel(k,rqm):
    k1=k
    sk=addr_storage[k1]
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

def update_channel_k_addr(x,c,k):
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

    task_dict[x]=[0,k]#0表示请求地址，2表示请求内容，k表示频道

    c=0%256#数量

    ccl = [0,x0,x1,c]#四字节，什么请求，什么回执标记，需要多少条
    bcc = bytes(ccl)

    rqm=bcc+k#k表示哪个频道

    send_to_channel(kt_channel,rqm)


def front_end():
    # while True:
    print(f"front end {port_offset}")
    print(f"front end {port_offset==1}")
    if port_offset==1 or port_offset==2:#send request
        print("??")
        k=b"football"
        x=1#0->65535
        c=0%256
        print(f"port{port_offset} update_k")
        update_channel_k_addr(x,c,k)
    if port_offset==2:
        while True:
            print(f"front_end()front_end_dm[0]->{front_end_dm[0]}")
            time.sleep(1)
            if(front_end_dm[0]==0):
                pass
            else:
                break
        #have update addr[k]
        
        print("front_end send msg request")
        if 1:#get msg[k]
            k=b"football"
            x=2
            if 1:
                xf=x
                x0=xf%256
                xf=xf//256
                x1=xf%256
            task_dict[x]=[2,k]#0表示请求地址，2表示请求内容，k表示频道
            print(f"front_end debug{task_dict}")
            c=0%256#数量
            ccl = [2,x0,x1,c]#四字节，什么请求，什么回执标记，需要多少条
            bcc=bytes(ccl)
            rqm=bcc+k#k表示哪个频道
            send_to_channel(k,rqm)
            print("front_end send msg request to k channel")


def thread_server():
    while True:#server loop
        try:
            data,client_addr=sock.recvfrom(4096)
            print(f"{data}{client_addr}")

            rq_addr_int=0
            rs_int=1
            rq_msg_int=2

            # rq_addr=bytes([0])
            # rs=bytes([1])#表示响应
            # rq_msg=bytes([2])#请求频道内容

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
                print("receive response")
                x0=data[1]
                x1=data[2]
                x=x0+x1*256#查是哪个任务，看看是回复给什么请求的响应 x类似于端口
                
                if 1:
                    print("x",x)
                    print(f"{task_dict}")
                    print(f"{x in task_dict}")
                    print(f"{task_dict[x]}")
                    task=task_dict[x]
                if task:
                    rq1=task[0]
                    k1=task[1]
                    print(f"rq1 k1{rq1}->{k1}")
                    if rq1==rq_addr_int:
                        print("debug 我们刚刚发给对方的是地址请求")
                        print(f"debug len(data)->{len(data)}")
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
                        if 1:#add
                            print("debug add")
                            print(f"{len(addr_list)}")
                            print(f"{addr_storage}")
                            
                            if k1 not in addr_storage:
                                addr_storage[k1]=set()
                            sk=addr_storage[k1]
                            for i in range(len(addr_list)):
                                print("debug add in..")
                                addr=addr_list[i]
                                sk.add(addr)

                            if port_offset==2:
                                front_end_dm[0]=1
                            print("debug add end")
                            print(f"front_end_dm[0]->{front_end_dm[0]}")
                            
                        if 0:#print
                            for addr in addr_list:
                                print(addr)
                    elif rq1==rq_msg_int:
                        print("我们收到了对内容请求的响应")
                        msg=data[4:]
                        print(f"k->{k1}->v->{msg}")
            elif head==rq_msg_int:#receive msg request
                print("receive msg request")
                print(f"data->{data}->")
                print(f"msg_storage->{msg_storage}")
                x0=data[1]
                x1=data[2]
                k=data[4:]


                c=0%256
                # rs=bytes([1])#表示响应
                bcc=[rs_int,x0,x1,c]
                rsm=b""
                rsm+=bytes(bcc)
                rsm+=msg_storage[k]
                sock.sendto(rsm,client_addr)
            print("debug try end")
            
        except Exception as e:
            # pass
            print(f"error@thread_server()->{e}")

def main():
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.bind(("::",this_port+int(port_offset)))
    if port_offset==1:#1号准备好消息
        k=b"football"
        msg_storage[k]=b"Paris Saint-Germain and Arsenal will compete for the Champions League title on May 31, 2026."
        # msg_storage[k]=b"PSG and Arsenal will vie for the Champions League title."

    # that_ip = '2001:19f0:1000:16bc:5400:06ff:fe29:acbc'#vps
    that_ip="::1"#local loop

    addr_storage[kt_channel]=set()
    if port_offset!=0:
        skt=addr_storage[kt_channel]
        addr_0_recevie=(that_ip,this_port+0)
        skt.add(addr_0_recevie)
    if 1:#update kt
        pass
    if port_offset==0:
        print("addr_0")
    else:#node_b
        print("node_b",port_offset)
    print("th start")
    thread_list=list()
    t=threading.Thread(target=thread_server, args=(), daemon=True)
    thread_list.append(t)
    t=threading.Thread(target=front_end,      args=(), daemon=True)
    thread_list.append(t)
    for i in range(len(thread_list)):
        t=thread_list[i]
        t.start()
    for i in range(len(thread_list)):
        t=thread_list[i]
        t.join()
if __name__ == "__main__":
    main()
