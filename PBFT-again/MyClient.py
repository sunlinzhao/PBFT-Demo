from socket import *
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import msgpack
import queue
import random
import time
# 本地导入
from MyUtils import get_free_port
from MyUtils import calculate_tolerance

# 创建日志对象
logger = logging.getLogger()

class Client(threading.Thread):
    def __init__(self, i, signature, local_port_listen, ips_ports, all_lock):
        threading.Thread.__init__(self)
        self.i = i
        self.signature = signature  # 签名信息（用随机数代替）
        self.ips_ports = ips_ports
        self.local_port_listen = local_port_listen
        # 无需传参的属性
        self.local_ip = '127.0.0.1'
        self.BUF_LEN = 512
        self.listen_num = 10000
        self.rec_count = []
        self.rec_flag = []
        self.lock_count = threading.RLock()
        self.lock_flag = threading.RLock()

        self.all_lock = all_lock

        # 创建线程池，最多维护400个线程，
        self.pool = ThreadPoolExecutor(400)

    def run(self):
        # 写入日志,节点启动时间
        logger.info(f'| Client [{self.i}] was established !')
        listen_socket = self.create_socket(self.local_ip, self.local_port_listen)
        # 进入监听状态
        listen_socket.listen(self.listen_num)
        logger.info(f'| Client [{self.i}] is listening!')
        while True:
            # 返回的 dataSocket 用来通信、传输数据
            dataSocket, addr = listen_socket.accept()
            # logger.info(f'| Client [{self.i}] linked to [{addr}] !')
            # 尝试读取对方发送的消息, BUF_LEN 指定从接收缓冲里最多读取多少字节。阻塞方式
            recved = dataSocket.recv(self.BUF_LEN)
            msg = msgpack.unpackb(recved)
            logger.info(f'Client [{self.i}] has received message :{msg["r"]}, from {msg["addr"]} with number {msg["number"]}')
            self.excute(msg)



    def find_vn(self, number):
        index = 0
        for item in self.rec_count:
            if number == item[0]:
                return index
            index += 1
        return None

    def excute(self, msg):
        tag = msg['tag']
        if tag == 'send_req':
            target = self.send_request
            args = (self.ips_ports[random.randint(0, len(self.ips_ports)-1)],)
            self.pool.submit(target, args[0])
        if tag == 'REPLY':
            self.pool.submit(self.process_REPLY, msg)

    def process_REPLY(self, msg):
        index = self.find_vn(msg['number'])
        if index == None:
            q = queue.Queue()
            q.put(msg)
            with self.lock_count:
                self.rec_count.append([msg['number'], q, False])
        else:
            with self.lock_count:
                self.rec_count[index][1].put(msg)
            if self.rec_count[index][1].qsize() >= calculate_tolerance(len(self.ips_ports)) + 1 and \
                    self.rec_count[index][2] == False:
                logger.info(f'Number {msg["number"]} has reached an agreement ! ')
                self.rec_count[index][2] = True
                # 编号加入已共识集合，避免重复计算
                with self.lock_flag:
                    self.rec_flag.append(self.rec_count[index][0])

    def send_request(self, dest_addr):
        with self.all_lock:
            # 获得可用端口号
            free_port = get_free_port()
            # 创建socket
            my_socket = self.create_socket(self.local_ip, free_port)
        # 打包消息
        REQUEST = {'tag': 'REQUEST',
                   'i': self.i,
                   'signature': self.signature,
                   'addr': (self.local_ip, self.local_port_listen)
                   }
        req_msg = msgpack.packb(REQUEST)
        my_socket.connect(dest_addr)
        # 发送请求消息
        my_socket.send(req_msg)
        # 假关闭
        my_socket.shutdown(SHUT_RDWR)
        time.sleep(0.001)
        # 关闭连接
        my_socket.close()
        time.sleep(random.uniform(0.001, 0.005))  # 防止太快，端口被占用完

    def create_socket(self, local_ip, local_port):
        # 实例化一个 socket 对象，指明TCP协议
        listenSocket = socket(AF_INET, SOCK_STREAM)
        # TCP 默认1为阻塞方式，0为非阻塞方式
        # listenSocket.setblocking(0)
        # listenSocket.settimeout(5)  # 设置超时等待时间
        # socket 绑定地址和端口
        listenSocket.bind((local_ip, local_port))
        # 设置 SO_REUSEADDR 选项，以便在关闭连接后能够快速重新绑定相同的地址和端口号
        listenSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return listenSocket
