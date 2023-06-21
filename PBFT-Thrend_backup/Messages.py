import time


class REQUEST(object):
    tag = 'REQUEST'
    t = time.time()  # 时间戳

    def __init__(self, o, i, sign, addr):
        self.o = o  # 操作类型
        self.i = i  # 客户端编号
        self.sign = sign  # 签名
        self.addr = addr


class PRE_PREPARE(object):
    tag = 'PRE_PREPARE'

    def __init__(self, v, n, d, sign, m):
        self.v = v  # 当前视图编号
        self.n = n  # 主节点给请求分配的编号
        self.d = d  # 请求消息的摘要
        self.sign = sign  # 签名
        self.m = m  # 客户端请求消息


class PREPARE(object):
    tag = 'PREPARE'

    def __init__(self, v, n, d, i, sign):
        self.v = v  # 当前视图编号
        self.n = n  # 主节点给请求分配的编号
        self.d = d  # 请求消息的摘要
        self.i = i  # 副本编号
        self.sign = sign  # 签名


class COMMIT(object):
    tag = 'COMMIT'

    def __init__(self, v, n, d, i, sign):
        self.v = v  # 当前视图编号
        self.n = n  # 主节点给请求分配的编号
        self.d = d  # 请求消息的摘要
        self.i = i  # 副本编号
        self.sign = sign  # 签名


class REPLY(object):
    tag = 'REPLY'

    def __init__(self, v, t, c, i, r, sign):
        self.v = v  # 当前视图编号
        self.t = t
        self.c = c  # 客户端编号
        self.i = i  # 副本编号
        self.r = r  # 请求操作执行结果
        self.sign = sign  # 签名


class VIEW_CHANGE(object):
    tag = 'VIEW_CHANGE'

    def __init__(self, v, n, C, P, i, sign):
        self.v = v  # 下一个视图编号
        self.n = n  # 消息序列号
        self.C = C  # stable checkpoint消息的集合
        self.P = P  # n 之后所有已经达到 prepared状态消息的集合
        self.i = i  # 副本编号
        self.sign = sign  # 签名


class NEW_VIEW(object):
    tag = 'NEW_VIEW'

    def __init__(self, v, V, O, sign):
        self.v = v  # 下一个视图编号
        self.V = V  # 新主节点收到的(包括自己发送的) VIEW-CHANGE 消息集合
        self.O = O  # PRE-PREPARE 状态的消息集合，保证视图变更后 P 集合中的消息安全
        self.sign = sign  # 签名


