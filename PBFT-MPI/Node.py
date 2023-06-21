import pickle

from Message import *
import hashlib


class Client(object):
    def __init__(self, i, signature):
        self.i = i
        self.signature = signature  # 签名信息（用随机数代替）

    def send_request(self, op, dest):
        pass


class Server(object):
    history_rec_pre_prepare = []  # 历史收到的 PRE_PREPARE 消息
    history_rec_prepare = []  # 历史收到的 PREPARE 消息
    history_rec_commit = []  # 历史收到的 COMMIT 消息

    def __init__(self, i, v, n, waterline, signature):
        self.i = i
        self.v = v  # 节点当前视图
        self.n = n
        self.waterline = waterline  # 水线
        self.signature = signature  # 签名信息（用随机数代替）

    def check_rec(self, message, sign_book, N):  # 校验消息的正确性 sign_book：节点签名列表 N：总节点数
        if message.tag == 'REQUEST':
            if message.sign != sign_book[message.i]:
                return False
            else:
                return True
        if message.tag == 'PRE_PREPARE':
            # 计算消息摘要
            digest = hashlib.sha256(pickle.dumps(message.m))
            digest = digest.hexdigest()
            if message.sign != sign_book[self.v % N]:  # 检查签名是否正确，因为时是主节点发送的消息，所以通过视图编号确认节点编号
                print('error signature!')
                return False
            elif message.d != digest:  # 消息摘要用hash值代替，确保消息的完整性
                print(f'error message digest!')
                return False
            elif message.v != self.v:  # 检查视图是否一致
                print('error view!')
                return False
            elif message.n < self.waterline[0] or message.n > self.waterline[1]:  # 判断是否不在水线范围内
                print('error waterline!')
                return False
            elif not self.nv_not_d(message):
                print('receive again!')
                return False
            else:
                return True
        if message.tag == 'PREPARE' or 'COMMIT':
            if message.sign != sign_book[message.i]:  # 检查签名是否正确
                return False
            elif message.d != self.find_nv(message.n, message.v):  # 检查摘要是否一致
                return False
            elif message.v != self.v:  # 检查视图是否一致
                return False
            elif message.n < self.waterline[0] or message.n > self.waterline[1]:  # 判断是否不在水线范围内
                return False
            else:
                return True
        if message.tag == 'VIEW_CHANGE':
            if message.sign != sign_book[message.i]:  # 检查签名是否正确
                return False
            return True
        if message.tag == 'NEW_VIEW':
            if message.sign != sign_book[self.v % N]:  # 检查签名是否正确，因为时是主节点发送的消息，所以通过视图编号确认节点编号
                return False
            return True

    def find_nv(self, n, v):  # 找到相同编号 n,v 的 Pre-Prepare 消息
        if len(self.history_rec_pre_prepare) == 0:
            return None
        else:
            for temp in self.history_rec_pre_prepare:
                if temp.n == n and temp.v == v:
                    return temp.d

    def nv_not_d(self, message):  # 判断是否接受过相同序号n v，但时不同摘要d
        if len(self.history_rec_pre_prepare) == 0:
            return True
        else:
            for temp in self.history_rec_pre_prepare:
                if temp.n == message.n and temp.v == message.v and temp.d != message.d:
                    return False
            return True

    def rec_request(self, source):
        pass

    def send_pre_prepare(self, request_message, dest):
        pass

    def rec_pre_prepare(self, source):
        pass
