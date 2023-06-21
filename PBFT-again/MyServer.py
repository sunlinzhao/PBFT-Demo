from concurrent.futures import ThreadPoolExecutor
from socket import *
import threading
import logging
import hashlib
import msgpack
import random
import queue
import math
import time
import os
# 本地导入
from MyUtils import get_free_port
from MyUtils import calculate_tolerance

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
path = 'log\\' + 'mylog - INFO - ' + name + '.log'
file = os.open(path, os.O_CREAT)
os.close(file)
file_handler = logging.FileHandler(path)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Server(threading.Thread):
    waterline = [0, 100]  # 水线

    def __init__(self, i, signature, local_ip, local_port_listen, sever_addrs, sign_book, N, all_lock):
        threading.Thread.__init__(self)
        self.i = i
        self.signature = signature  # 签名信息（用随机数代替）
        self.local_ip = local_ip
        self.local_port_listen = local_port_listen
        self.sever_addrs = sever_addrs
        self.sign_book = sign_book
        self.N = N

        # 无需传参的属性
        self.n = 0
        self.v = 0
        self.BUF_LEN = 512
        self.listen_num = 10000  # 应当设置的大一点，因为并行处理，可能出现线程的端口抢占
        # 相同 v_n 消息队列
        self.rec_vn = []
        # vn 编号的客户端地址
        self.vn_client_addr = []
        # 线程锁
        self.lock_client_addr = threading.RLock()
        self.lock_rec_vn = threading.RLock()
        # 线程池
        self.pool = ThreadPoolExecutor(1000)

        self.all_lock = all_lock

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
            rec_msg = msgpack.unpackb(recved)
            self.excute(rec_msg)

    def excute(self, msg):
        if msg['tag'] == 'REQUEST':
            self.pool.submit(self.process_REQUEST, msg)
        if msg['tag'] == 'PRE_PREPARE':
            self.pool.submit(self.process_PRE_PREPARE, msg)
        if msg['tag'] == 'PREPARE':
            self.pool.submit(self.process_PREPARE, msg)
        if msg['tag'] == 'COMMIT':
            self.pool.submit(self.process_COMMIT, msg)

    def process(self, number, tag):
        index = self.find_vn(number)
        if index != None:
            q = self.rec_vn[index][1]
            if not q["pre-prepare"].empty() and tag=='pre-prepare':
                # print(q["pre-prepare"].get())
                pre_msg = q["pre-prepare"].get()
                # self.broadcast(pre_msg)
                self.pool.submit(self.broadcast, pre_msg)
            if not q['prepare'].empty() and tag=='prepare':
                prepare_msg = q["prepare"].get()
                # self.broadcast(prepare_msg)
                self.pool.submit(self.broadcast, prepare_msg)
            if not q['commit'].empty() and tag=='commit':
                commit_msg = q['commit'].get()
                # self.broadcast(commit_msg)
                self.pool.submit(self.broadcast, commit_msg)
            if not q['reply'].empty() and tag == 'reply':
                reply_msg = q['reply'].get()
                pos = self.find_addr(number)
                logger.info(f'@@@')
                # print(f'{self.i} - - - {self.vn_client_addr[pos][1]}')
                # self.send_msg(reply_msg, self.vn_client_addr[pos][1])
                self.pool.submit(self.send_msg, reply_msg, self.vn_client_addr[pos][1])

        else:
            print(f'{number} is not exsit!')

    # def process_b(self, number):
    #     index = self.find_vn(number)
    #     if index != None:
    #         q = self.rec_vn[index][1]
    #         # if self.i == self.v % self.N:
    #         #     print(self.rec_vn[index][1]["commit"].qsize())
    #         #     time.sleep(random.uniform(0, 0.5))
    #         while not q['commit'].empty():
    #             commit_msg = q['commit'].get()
    #             print(f'{self.i} get commmt')


    def clear_queue(self, q):
        while not q.empty():
            item = q.get()

    def find_addr(self, number):
        index = 0
        for item in self.vn_client_addr:
            if number == item[0]:
                return index
            index += 1
        return None

    def find_vn(self, number):
        index = 0
        for item in self.rec_vn:
            if number == item[0]:
                return index
            index += 1
        return None

    def create_socket(self, local_ip, local_port):
        # 实例化一个 socket 对象，指明TCP协议
        listenSocket = socket(AF_INET, SOCK_STREAM)
        # listenSocket.settimeout(5)  # 设置超时等待时间
        # socket 绑定地址和端口
        listenSocket.bind((local_ip, local_port))
        # 设置 SO_REUSEADDR 选项，以便在关闭连接后能够快速重新绑定相同的地址和端口号
        listenSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return listenSocket

    def send_msg(self, msg, dest_addrs):
        # 序列化
        req_msg = msgpack.packb(msg)
        with self.all_lock:
            # 获取可用端口号
            free_port = get_free_port()
            # 生成 socket
            my_socket = self.create_socket(self.local_ip, free_port)
        # 建立连接
        my_socket.connect(tuple(dest_addrs))
        # 转发送给当前 leader
        my_socket.send(req_msg)
        # 假关闭，关闭写入和和可读通道
        my_socket.shutdown(SHUT_RDWR)
        time.sleep(0.001)
        # 关闭连接
        my_socket.close()
        time.sleep(random.uniform(0.001, 0.005))  # 防止太快，端口被占用完

    def broadcast(self, msg):
        # 序列化
        msg = msgpack.packb(msg)
        for i in range(self.N):
            if i != self.i:
                with self.all_lock:
                    # 获取可用端口号
                    free_port = get_free_port()
                    # 生成 socket
                    my_socket = self.create_socket(self.local_ip, free_port)
                # 建立连接
                my_socket.connect((self.sever_addrs[i]))
                # 发送消息
                my_socket.send(msg)
                # 假关闭，关闭写入和和可读通道
                my_socket.shutdown(SHUT_RDWR)
                time.sleep(0.001)
                # 关闭连接
                my_socket.close()
                time.sleep(random.uniform(0.001, 0.005))  # 防止太快，端口被占用完

    def process_REQUEST(self, msg):
        # 如果是请求消息，则分配视图编号和消息编号，并加入消息队列
        if (self.v % self.N) == self.i:  # 判断 Leader
            # 分配编号
            number = [self.v, self.n]
            # 更新消息编号
            self.n = self.n + 1
            # 记录客户端地址
            with self.lock_client_addr:
                self.vn_client_addr.append((number, msg['addr']))
            # 生成消息摘要
            sha256 = hashlib.sha256(msgpack.packb(msg))
            digest = sha256.hexdigest()
            # 生成 PRE-PREPARE 消息包
            PRE_PREPARE = {'tag': 'PRE_PREPARE',
                           'number': number,
                           'digest': digest,
                           'signature': self.signature,
                           'msg': msg,
                           'addr': (self.local_ip, self.local_port_listen)
                           }
            index = self.find_vn(number)
            if index == None:  # 判断是否有已存在重复的编号
                # 放入队列
                q = {"pre-prepare": queue.Queue(),
                     "prepare": queue.Queue(),
                     "commit": queue.Queue(),
                     "reply": queue.Queue()
                     }
                q["pre-prepare"].put(PRE_PREPARE)
                with self.lock_rec_vn:
                    self.rec_vn.append([number, q])
            else:
                with self.lock_rec_vn:
                    self.rec_vn[index][1]["pre-prepare"].put(PRE_PREPARE)
            # 启动子线程处理器去处理 相同 number 的事务
            self.pool.submit(self.process, number, 'pre-prepare')
        else:
            # 转发请求给 Leader
            # self.send_msg(msg, self.sever_addrs[self.v % self.N])
            self.pool.submit(self.send_msg, msg, self.sever_addrs[self.v % self.N])


    def process_PRE_PREPARE(self, msg):
        number = msg['number']
        # 记录客户端地址
        with self.lock_client_addr:
            self.vn_client_addr.append((number, msg['msg']['addr']))
        logger.info(f'{self.i} <---- {self.v % self.N} with {msg["tag"]} {number}')
        # 生成 PREPARE 消息包
        PREPARE = {'tag': 'PREPARE',
                   'number': number,
                   'i': self.i,
                   'digest': msg['digest'],
                   'signature': self.signature,
                   'addr': (self.local_ip, self.local_port_listen)
                   }
        index = self.find_vn(number)
        if index == None:  # 判断是否有已存在重复的编号
            # 放入队列
            q = {"pre-prepare": queue.Queue(),
                 "prepare": queue.Queue(),
                 "commit": queue.Queue(),
                 "reply": queue.Queue()
                 }
            q["prepare"].put(PREPARE)
            with self.lock_rec_vn:
                self.rec_vn.append([number, q])
        else:
            with self.lock_rec_vn:
                self.rec_vn[index][1]["prepare"].put(PREPARE)
        # 启动子线程处理器去处理 相同 number 的事务
        self.pool.submit(self.process, number, 'prepare')

    def process_PREPARE(self, msg):
        number = msg['number']
        logger.info(f'{self.i} <---- {msg["i"]} with {msg["tag"]} - {number}')

        index = self.find_vn(number)
        if index == None:
            q = {"pre-prepare": queue.Queue(),
                 "prepare": queue.Queue(),
                 "commit": queue.Queue(),
                 "reply": queue.Queue()
                 }
            q["prepare"].put(msg)
            with self.lock_rec_vn:
                self.rec_vn.append([number, q])
        else:
            with self.lock_rec_vn:
                self.rec_vn[index][1]["prepare"].put(msg)
            if self.rec_vn[index][1]['prepare'].qsize() >= 2 * calculate_tolerance(self.N):  # 收到大多数消息

                # 清空 prepare 消息队列
                with self.lock_rec_vn:
                    self.clear_queue(self.rec_vn[index][1]['prepare'])
                # 生成 COMMIT 消息包
                COMMIT = {'tag': 'COMMIT',
                          'number': number,
                          'i': self.i,
                          'digest': msg['digest'],
                          'signature': self.signature,
                          'addr': (self.local_ip, self.local_port_listen)
                          }
                with self.lock_rec_vn:
                    # 放入消息队列
                    self.rec_vn[index][1]["commit"].put(COMMIT)
                # 启动子线程处理器去处理 相同 number 的事务
                self.pool.submit(self.process, number, 'commit')
                # 更新视图编号
                self.v = self.v + 1

    def process_COMMIT(self, msg):
        number = msg['number']
        logger.info(f'{self.i} <---- {msg["i"]} with {msg["tag"]} - {number}')
        index = self.find_vn(number)
        if index == None:
            q = {"pre-prepare": queue.Queue(),
                 "prepare": queue.Queue(),
                 "commit": queue.Queue(),
                 "reply": queue.Queue()
                 }
            q["commit"].put(msg)
            with self.lock_rec_vn:
                self.rec_vn.append([number, q])
        else:
            with self.lock_rec_vn:
                self.rec_vn[index][1]["commit"].put(msg)
            if self.rec_vn[index][1]['commit'].qsize() >= 2 * calculate_tolerance(self.N):  # 收到大多数消息
                # 清空 commit 消息队列
                with self.lock_rec_vn:
                    self.clear_queue(self.rec_vn[index][1]['commit'])
                # 生成 REPLY 消息包
                REPLY = {'tag': 'REPLY',
                         'number': number,
                         't': time.time(),
                         'i': self.i,
                         'r': 'result',
                         'signature': self.signature,
                         'addr': (self.local_ip, self.local_port_listen)
                         }
                # 放入消息队列
                with self.lock_rec_vn:
                    self.rec_vn[index][1]["reply"].put(REPLY)
                # 启动子线程处理器去处理 相同 number 的事务
                self.pool.submit(self.process, number, 'reply')

    def check(self, msg):
        tag = msg['tag']
        if tag == 'REQUEST':
            if msg['signature'] == 'I am a Client':
                return False
        return True
