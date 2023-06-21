from socket import *
import threading
import logging
import pickle
import random
# 本地导入
from Messages import *
from utils import get_free_port

# 创建日志对象
logger = logging.getLogger()

class Client(threading.Thread):
    def __init__(self, i, signature, local_port_listen, ips_ports):
        threading.Thread.__init__(self)
        self.i = i
        self.signature = signature  # 签名信息（用随机数代替）
        self.ips_ports = ips_ports
        self.local_port_listen = local_port_listen
        # 无需传参的属性
        self.local_ip = '127.0.0.1'
        self.dest_ips = []
        self.dest_ports = []
        self.BUF_LEN = 512
        self.listen_num = 1000

    def run(self):
        num = 0
        config_num = 0
        flag = 0
        # 写入日志,节点启动时间
        logger.info(f'| Client [{self.i}] was established !')
        listen_socket = self.create_socket(self.local_ip, self.local_port_listen)
        # 进入监听状态
        listen_socket.listen(self.listen_num)
        logger.info(f'| Client [{self.i}] is listening!')
        while True:
            # 发送请求消息
            self.excute('send_req', self.ips_ports[random.randint(0, len(self.ips_ports)-1)])
            # 返回的 dataSocket 用来通信、传输数据
            dataSocket, addr = listen_socket.accept()
            # logger.info(f'| Client [{self.i}] linked to [{addr}] !')
            # 尝试读取对方发送的消息, BUF_LEN 指定从接收缓冲里最多读取多少字节。阻塞方式
            recved = dataSocket.recv(self.BUF_LEN)
            recved = pickle.loads(recved)
            from_addr = recved['addr']
            msg = recved['content']
            logger.info(f'Client [{self.i}] has received {num}th message :{msg.r}, from {from_addr}')
            num += 1
            config_num = int(num / 3)
            if config_num > flag:
                print(f'{config_num} 个请求达成了共识！')
                flag = config_num
            # dataSocket.close()
            time.sleep(0.5)  # 防止太快，端口被占用完

    def excute(self, op, dest_addr):
        if op == 'send_req':
            thr = threading.Thread(target=self.send_request, args=(dest_addr,))
            thr.start()
            thr.join()
    def send_request(self, dest_addr):
        # 获得可用端口号
        free_port = get_free_port()
        # 创建socket
        my_socket = self.create_socket(self.local_ip, free_port)
        # 打包消息
        req_msg = REQUEST('TEST', self.i, self.signature, (self.local_ip, self.local_port_listen))
        req_msg = {'content':req_msg, 'addr':(self.local_ip, self.local_port_listen)}
        req_msg = pickle.dumps(req_msg)
        my_socket.connect(dest_addr)
        # 发送请求消息
        my_socket.send(req_msg)
        # 假关闭
        my_socket.shutdown(SHUT_RDWR)
        # 关闭连接
        my_socket.close()
        time.sleep(0.5)  # 防止太快，端口被占用完

    def create_socket(self, local_ip, local_port):
        # 实例化一个 socket 对象，指明TCP协议
        listenSocket = socket(AF_INET, SOCK_STREAM)
        # TCP 默认1为阻塞方式，0为非阻塞方式
        # self.listenSocket.setblocking(1)
        # listenSocket.settimeout(5)  # 设置超时等待时间
        # socket 绑定地址和端口
        listenSocket.bind((local_ip, local_port))
        return listenSocket
