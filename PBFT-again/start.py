from MyClient import Client
from MyServer import Server
from MyUtils import get_free_port
import random
import time
import matplotlib.pyplot as plt
import threading

all_lock = threading.RLock()

# 本地 ip
local_ip_base = '127.0.0.1'

# 服务端节点数量
N = 16
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
    s = Server(i, sign, local_ip_base, listen_port, ips_ports, signature_book, N, all_lock)
    s.start()

# 建立客户端
c1 = Client(0, 'I am a Client', get_free_port(), ips_ports, all_lock)
c1.start()

def gogo(num):
    # for i in range(num):
    while True:
        c1.excute({'tag': 'send_req'})
        time.sleep(0.001)  # 防止太快，端口被占用完
# # 发送请求消息
th = threading.Thread(target=gogo, args=(50, ))
th.start()

def draw(c):
    plt.style.use('seaborn')  # 设置图表风格
    plt.figure()  # 创建图表对象
    plt.ion()  # 开启交互模式
    y1 = []
    # y2 = []
    while True:
        y1.append(len(list(c.rec_flag)))
        # y2.append(len(list(c.rec_count)))
        x1 = [i for i in range(len(y1))]
        # x2 = [i for i in range(len(y2))]

        plt.plot(x1, y1, color='blue')
        # plt.plot(x2, y2, color='red')

        plt.tight_layout()  # 调整子图之间的间距
        plt.draw()
        plt.pause(1)  # 暂停1秒
    plt.ioff()  # 关闭交互模式
    plt.show()  # 显示最终图表

thr = threading.Thread(target=draw, args=(c1,))
thr.start()

th.join()
thr.join()