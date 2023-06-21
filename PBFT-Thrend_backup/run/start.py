from Clients import Client
from Servers import Server
from utils import get_free_port
import random
import time

# 本地 ip
local_ip_base = '127.0.0.1'

# 服务端节点数量
N = 4
# 生成节点监听地址列表
ips_ports = []
# 签名册
signature_book = []
for i in range(N):
    sign = random.random()
    signature_book.append(sign)
    listen_port = get_free_port()
    ips_ports.append((local_ip_base, listen_port))
    # 建立服务端
    s = Server(i, sign, local_ip_base, listen_port, ips_ports, signature_book, N)
    s.start()

# 建立客户端
c1 = Client(0, 'i am client', 30000, ips_ports)
c1.start()
