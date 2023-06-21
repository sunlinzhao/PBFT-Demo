from socket import *
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import threading
import logging
import hashlib
import pickle
import math
import time
import os
# 本地导入
from Messages import *
from utils import get_free_port


'''日志的配置信息只设置一次即可，当然如果项目大，有不同的需求，可以写在配置文件里'''
# 创建日志对象
logger = logging.getLogger()
# 设置日志等级
logger.setLevel(logging.INFO)
# 配置日志格式
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
ansi_formatter = logging.Formatter('\033[32m%(asctime)s %(levelname)s %(message)s\033[0m')
# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(ansi_formatter)
logger.addHandler(console_handler)
# 文件输出
name = str(time.time())
path = 'log\\' + 'mylog - ' +name + '.log'
file = os.open(path, os.O_CREAT)
os.close(file)
file_handler = logging.FileHandler(path)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Server(threading.Thread):
    waterline = [0, 100]  # 水线

    def __init__(self, i, signature, local_ip, local_port_listen, sever_addrs, sign_book, N):
        threading.Thread.__init__(self)
        self.i = i
        self.signature = signature  # 签名信息（用随机数代替）
        self.local_ip = local_ip
        self.local_port_listen = local_port_listen
        self.sever_addrs = sever_addrs
        self.sign_book = sign_book
        self.N = N

        # 无需传参的属性
        self.v = 0  # 节点当前视图
        self.n = 0
        self.BUF_LEN = 512
        self.listen_num = 1000   # 应当设置的大一点，因为并行处理，可能出现线程的端口抢占
        self.history_pre_prepare = np.zeros((self.N, self.waterline[1]), dtype=PRE_PREPARE)  # 历史收到的 PRE_PREPARE 消息 N x waterline[1]
        self.counter_prepare = [set({}) for i in range(self.waterline[1])] # prepare 消息计数器
        self.counter_commit = [set({}) for i in range(self.waterline[1])]  # commit 消息计数器
        self.counter_view_change = [set({}) for i in range(self.waterline[1])]  # view_change 消息计数器
        self.client_addrs = np.zeros((self.N, self.waterline[1]), dtype=tuple) # 记录客户端地址

        self.lock = threading.RLock()
        self.pool = ThreadPoolExecutor(10)

    def run(self):
        # 写入日志,节点启动时间
        logger.info(f'| Server [{self.i}] was established !')
        # 创建socket
        listen_socket = self.create_socket(self.local_ip, self.local_port_listen)
        # 进入监听状态
        listen_socket.listen(self.listen_num)
        logger.info(f'| Server [{self.i}] is listening !')
        while True:
            # 返回的 dataSocket 用来通信、传输数据
            dataSocket, addr = listen_socket.accept()
            # logger.info(f'| Server [{self.i}] linked to {addr} !')
            # 尝试读取对方发送的消息, BUF_LEN 指定从接收缓冲里最多读取多少字节。阻塞方式
            recved = dataSocket.recv(self.BUF_LEN)
            rec_msg = pickle.loads(recved)
            self.excute(rec_msg)

    def excute(self, rec_msg):
        msg = rec_msg['content']
        if msg.tag == 'REQUEST':
            with self.lock:
                target = self.process_request
                args = rec_msg
                self.pool.submit(target, args)
        elif msg.tag == 'PRE_PREPARE':
            with self.lock:
                target = self.process_pre_prepare
                args = rec_msg
                self.pool.submit(target, args)
        elif msg.tag == 'PREPARE':
            with self.lock:
                target = self.process_prepare
                args = rec_msg
                self.pool.submit(target, args)
        elif msg.tag == 'COMMIT':
            with self.lock:
                target = self.process_commit
                args = rec_msg
                self.pool.submit(target, args)
        elif msg.tag == 'VIEW_CHANGE':
            with self.lock:
                target = self.process_view_change
                args = rec_msg
                self.pool.submit(target, args)
        elif msg.tag == 'NEW_VIEW':
            with self.lock:
                target = self.process_new_view
                args = rec_msg
                self.pool.submit(target, args)
        else:
            pass

    def process_request(self, rec_msg):
        addr = rec_msg['addr']
        msg = rec_msg['content']
        logger.info(f'| Server [{self.i}] has received <{msg.tag}> message from Client [{msg.i}] whit address {addr}')

        if self.check_rec(msg, self.sign_book, self.N):  # 验证消息
            if self.i == (self.v % self.N):   # 判断自己是否是当前视图 Leader
                # 记录客户端地址
                self.client_addrs[self.v % self.N][self.n % self.waterline[1]] = msg.addr
                # 生成消息摘要
                sha256 = hashlib.sha256(pickle.dumps(msg))
                digest = sha256.hexdigest()
                # 生成消息
                pre_pre_msg = PRE_PREPARE(self.v, self.n, digest, self.signature, msg)
                # 记录 PRE-PREPARE 消息
                self.history_pre_prepare[self.v % self.N][self.n % self.waterline[1]] = pre_pre_msg
                print(self.history_pre_prepare)
                # 更新消息编号
                self.n = self.n + 1
                # 打包消息
                pre_pre_msg = {'content': pre_pre_msg, 'addr': (self.local_ip, self.local_port_listen)}
                pre_pre_msg = pickle.dumps(pre_pre_msg)
                for i in range(self.N):
                    if i != self.i:
                        # 获取可用端口号
                        free_port = get_free_port()
                        # 生成 socket
                        my_socket = self.create_socket(self.local_ip, free_port)
                        # 建立连接
                        my_socket.connect((self.sever_addrs[i]))
                        # 发送消息
                        my_socket.send(pre_pre_msg)
                        # 假关闭，关闭写入和和可读通道
                        my_socket.shutdown(SHUT_RDWR)
                        # 关闭连接
                        my_socket.close()
                        time.sleep(0.5)  # 防止太快，端口被占用完
            else:
                # 获取可用端口号
                free_port = get_free_port()
                # 生成 socket
                my_socket = self.create_socket(self.local_ip, free_port)
                # 建立连接
                my_socket.connect((self.sever_addrs[self.v % self.N]))
                # 打包消息
                req_msg = {'content':msg, 'addr':(self.local_ip, self.local_port_listen)}
                req_msg = pickle.dumps(req_msg)
                # 转发送给当前 leader
                my_socket.send(req_msg)
                # 假关闭，关闭写入和和可读通道
                my_socket.shutdown(SHUT_RDWR)
                # 关闭连接
                my_socket.close()
                time.sleep(0.5)  # 防止太快，端口被占用完
        else:
            pass

    def process_pre_prepare(self, rec_msg):
        addr = rec_msg['addr']
        msg = rec_msg['content']
        logger.info(f'| Server [{self.i}] has received <{msg.tag}> message from Node [{msg.v % self.N}] with address {addr}')
        if self.check_rec(msg, self.sign_book, self.N):  # 验证消息
            # 记录客户端地址
            self.client_addrs[msg.v % self.N][msg.n % self.waterline[1]] = msg.m.addr
            # 记录 PRE-PREPARE 消息
            self.history_pre_prepare[msg.v % self.N][msg.n % self.waterline[1]] = msg
            # 重置 prepare 消息计数器，为下一阶段使用做准备
            self.counter_prepare[msg.n % self.waterline[1]].clear()
            # 生成消息
            pre_msg = PREPARE(msg.v, msg.n, msg.d, self.i, self.signature)
            # 打包消息
            pre_msg = {'content': pre_msg, 'addr': ((self.local_ip, self.local_port_listen))}
            pre_msg = pickle.dumps(pre_msg)
            # 依次发送消息
            for i in range(self.N):
                if i != self.i:  # 给除了自己以外的服务节点发送消息
                    # 获取可用端口号
                    free_port = get_free_port()
                    # 生成 socket
                    my_socket = self.create_socket(self.local_ip, free_port)
                    # 建立连接
                    my_socket.connect((self.sever_addrs[i]))
                    # 发送消息
                    my_socket.send(pre_msg)
                    # 假关闭，关闭写入和和可读通道
                    my_socket.shutdown(SHUT_RDWR)
                    # 关闭连接
                    my_socket.close()
                    time.sleep(0.5)  # 防止太快，端口被占用完
        else:
            pass

    def process_prepare(self, rec_msg):
        addr = rec_msg['addr']
        msg = rec_msg['content']
        logger.info(f'| Server [{self.i}] has received <{msg.tag}> message from Node [{msg.i}] with address {addr}')
        if self.check_rec(msg, self.sign_book, self.N):  # 验证消息
            self.counter_prepare[msg.n % self.waterline[1]].add((msg.i, msg.v, msg.n))    # 消息计数，用集合类型统计不同消息个数
            if len(self.counter_prepare[msg.n % self.waterline[1]]) >= math.ceil(2 * (self.N-1) / 3):  # 由于要算上自己的一票，所以就不加一了
                print(f'Node [{self.i}] enter commit stage ! ')
                # 生成消息
                com_msg = COMMIT(msg.v, msg.n, msg.d, self.i, self.signature)
                # 打包消息
                com_msg = {'content': com_msg, 'addr': ((self.local_ip, self.local_port_listen))}
                com_msg = pickle.dumps(com_msg)
                for i in range(self.N):
                    if i != self.i:  # 给除了自己以外的服务节点发送消息
                        # 获取可用端口号
                        free_port = get_free_port()
                        # 生成 socket
                        my_socket = self.create_socket(self.local_ip, free_port)
                        # 建立连接
                        my_socket.connect((self.sever_addrs[i]))
                        # 发送消息
                        my_socket.send(com_msg)
                        # 假关闭，关闭写入和和可读通道
                        my_socket.shutdown(SHUT_RDWR)
                        # 关闭连接
                        my_socket.close()
                        time.sleep(0.5)  # 防止太快，端口被占用完
                # prepare 计数器重置，但是等到下次使用之前（pre_prepare 阶段），需要再次重置，因为达到数量后，后续消息依然会到来
                self.counter_prepare[msg.n % self.waterline[1]].clear()
                # commit 消息计数器重置，为下一阶段使用做准备
                self.counter_commit[msg.n % self.waterline[1]].clear()
            else:
                pass


    def process_commit(self, rec_msg):
        addr = rec_msg['addr']
        msg = rec_msg['content']
        logger.info(f'| Server [{self.i}] has received <{msg.tag}> message from Node [{msg.i}] with address {addr}')
        if self.check_rec(msg, self.sign_book, self.N):  # 验证消息
            self.counter_commit[msg.n % self.waterline[1]].add((msg.i, msg.v, msg.n))  # 消息计数，用集合类型统计不同消息个数
            if len(self.counter_commit[msg.n % self.waterline[1]]) >= math.ceil(2 * (self.N - 1) / 3):  # 由于要算上自己的一票，所以就不加一了
                print(f'Node [{self.i}] enter reply stage ! ')
                # 获取客户端编号
                c_pre = self.history_pre_prepare[msg.v % self.N][msg.n % self.waterline[1]]
                c = c_pre.m.i
                t = c_pre.m.t
                # 生成消息
                reply_msg = REPLY(msg.v, t, c, self.i, 'Result', self.signature)
                # 打包消息
                reply_msg = {'content': reply_msg, 'addr': ((self.local_ip, self.local_port_listen))}
                reply_msg = pickle.dumps(reply_msg)
                # 获取可用端口号
                free_port = get_free_port()
                # 生成 socket
                my_socket = self.create_socket(self.local_ip, free_port)
                # 建立连接
                my_socket.connect(self.client_addrs[msg.v % self.N][msg.n % self.waterline[1]])
                # print(self.client_addrs[msg.v % self.N][msg.n % self.waterline[1]])
                # 发送消息
                my_socket.send(reply_msg)
                # 假关闭，关闭写入和和可读通道
                my_socket.shutdown(SHUT_RDWR)
                # 关闭连接
                my_socket.close()
                # commit 消息计数器重置
                self.counter_commit[msg.n % self.waterline[1]].clear()
                time.sleep(0.5)   # 防止太快，端口被占用完
                # 更新视图编号
                self.v = self.v + 1
            else:
                pass

    def process_view_change(self, rec_msg):
        addr = rec_msg['addr']
        msg = rec_msg['content']
        logger.info(f'| Server [{self.i}] has received <{msg.tag}> message from Node [{msg.i}] with address {addr}')
        if self.check_rec(msg, self.sign_book, self.N):  # 验证消息
            self.counter_view_change[msg.n % self.waterline[1]].add((msg.i, msg.v, msg.n))  # 消息计数，用集合类型统计不同消息个数
            if len(self.counter_prepare[msg.n % self.waterline[1]]) >= math.ceil(2 * (self.N - 1) / 3):  # 由于要算上自己的一票，所以就不加一了
                print(f'Node [{self.i}] enter view_change stage ! ')
                if self.i == ((self.v + 1) % self.N):
                    self.v = (self.v + 1) % self.N
                    # 生成消息
                    new_view_msg = NEW_VIEW(self.v, self.counter_view_change, self.history_pre_prepare, self.signature)
                    # 打包消息
                    new_view_msg = {'content': new_view_msg, 'addr': ((self.local_ip, self.local_port_listen))}
                    new_view_msg = pickle.dumps(new_view_msg)
                    for i in range(self.N):
                        if i != self.i:  # 给除了自己以外的服务节点发送消息
                            # 获取可用端口号
                            free_port = get_free_port()
                            # 生成 socket
                            my_socket = self.create_socket(self.local_ip, free_port)
                            # 建立连接
                            my_socket.connect((self.sever_addrs[i]))
                            # 发送消息
                            my_socket.send(new_view_msg)
                            # 假关闭，关闭写入和和可读通道
                            my_socket.shutdown(SHUT_RDWR)
                            # 关闭连接
                            my_socket.close()
                            time.sleep(0.5)  # 防止太快，端口被占用完
                    # 重置计数器
                    self.counter_view_change[msg.n % self.waterline[1]].clear()
                else:
                    # 获取可用端口号
                    free_port = get_free_port()
                    # 生成 socket
                    my_socket = self.create_socket(self.local_ip, free_port)
                    # 建立连接
                    my_socket.connect((self.sever_addrs[(self.v + 1) % self.N]))
                    # 打包消息
                    vc_msg = {'content': msg, 'addr': (self.local_ip, self.local_port_listen)}
                    vc_msg = pickle.dumps(vc_msg)
                    # 转发送给当前 leader
                    my_socket.send(vc_msg)
                    # 假关闭，关闭写入和和可读通道
                    my_socket.shutdown(SHUT_RDWR)
                    # 关闭连接
                    my_socket.close()
                    time.sleep(0.5)  # 防止太快，端口被占用完
            else:
                pass

    def process_new_view(self, rec_msg):
        addr = rec_msg['addr']
        msg = rec_msg['content']
        logger.info(f'| Server [{self.i}] has received <{msg.tag}> message from Node [{msg.v % self.N}] with address {addr}')
        if self.check_rec(msg, self.sign_book, self.N):  # 验证消息
            self.v = msg.v
            self.O = msg.O

    def create_socket(self, local_ip, local_port):
        # 实例化一个 socket 对象，指明TCP协议
        listenSocket = socket(AF_INET, SOCK_STREAM)
        # listenSocket.settimeout(5)  # 设置超时等待时间
        # socket 绑定地址和端口
        listenSocket.bind((local_ip, local_port))
        return listenSocket


    def check_rec(self, message, sign_book, N):  # 校验消息的正确性 sign_book：节点签名列表 N：总节点数
        if message.tag == 'REQUEST':
            if message.sign != 'i am client':
                return False
        elif message.tag == 'PRE_PREPARE':
            # 计算消息摘要
            digest = hashlib.sha256(pickle.dumps(message.m))
            digest = digest.hexdigest()
            if message.sign != sign_book[message.v % N]:  # 检查签名是否正确，因为是主节点发送的消息，所以通过视图编号确认节点编号
                print(f'PRE_PREPARE error signature! - {message.sign} - {sign_book[message.v % N]}')
                return False
            if message.d != digest:  # 消息摘要用hash值代替，确保消息的完整性
                print(f'PRE_PREPARE error message digest!')
                return False
            if message.v != self.v:  # 检查视图是否一致
                print(f'PRE_PREPARE error view! - {message.v} - {self.v}')
                return False
            if message.n < self.waterline[0] or message.n > self.waterline[1]:  # 判断是否不在水线范围内
                print('PRE_PREPARE error waterline!')
                return False
        elif message.tag == 'PREPARE' or 'COMMIT':
            if message.sign != sign_book[message.i]:  # 检查签名是否正确
                print('PREPARE or COMMIT error signature!')
                return False
            if self.history_pre_prepare[message.v % self.N][message.n % self.waterline[1]] == 0:  # 先判断是否为空
                print('PREPARE or COMMIT null!')
                return False
            if message.d != self.history_pre_prepare[message.v % self.N][message.n % self.waterline[1]].d:  # 检查摘要是否一致
                print('PREPARE or COMMIT error digest!')
                return False
            if message.v != self.v:  # 检查视图是否一致
                print('PREPARE or COMMIT error view!')
                return False
            if message.n < self.waterline[0] or message.n > self.waterline[1]:  # 判断是否不在水线范围内
                print('PREPARE or COMMIT error waterline!')
                return False
        elif message.tag == 'VIEW_CHANGE':
            if message.sign != sign_book[message.i]:  # 检查签名是否正确
                return False
        elif message.tag == 'NEW_VIEW':
            if message.sign != sign_book[self.v % N]:  # 检查签名是否正确，因为是主节点发送的消息，所以通过视图编号确认节点编号
                return False
        return True
