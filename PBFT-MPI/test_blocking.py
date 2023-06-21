from Node import *
import mpi4py.MPI as MPI
import random
import numpy as np
import hashlib
import time
import math
import pickle
import json

import warnings

warnings.filterwarnings("ignore")

# 创建通信器和组
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
N = size - 1  # 服务端总节点数

# 分配一个共享内存窗口
win1 = MPI.Win.Allocate_shared(np.dtype('float64').itemsize * size, info=MPI.INFO_NULL, comm=comm)
win2 = MPI.Win.Allocate_shared(np.dtype('int64').itemsize * 2, info=MPI.INFO_NULL, comm=comm)

# 得到共享内存的地址
buf1, _ = win1.Shared_query(N)
signs = np.ndarray(buffer=buf1, dtype='float64', shape=(size,))

buf2, _ = win2.Shared_query(N)
waterline = np.ndarray(buffer=buf2, dtype='int64', shape=(2,))

# 初始化共享内存
if rank == 0:
    signs[:] = np.arange(size, dtype='float64')
    waterline[:] = np.arange(2, dtype='int64')
    waterline[0] = 0
    waterline[1] = 100

# 同步进程
comm.Barrier()

# 共识开始
if rank == N:  # 进程0作为客户端
    # 生成签名
    sig_c = random.random()
    signs[rank] = sig_c
    # 创建客户端对象
    cli = Client(rank, sig_c)
    # 客户端发送请求
    req_msg = REQUEST('This is a run!!!', rank, cli.signature)
    for i in range(N):
        req = comm.send(pickle.dumps(req_msg), i)

# Synchronize access to the window
win1.Fence()
win2.Fence()

if rank != N:
    # 生成签名
    sig_s = random.random()
    signs[rank] = sig_s
    # 创建服务器对象
    ser = Server(rank, 1, 0, waterline, sig_s)
    # 动态分配内存
    status = MPI.Status()
    comm.Probe(source=N, status=status)
    count = status.Get_count(MPI.BYTE)  # 获取接收到的个数
    rec_req = np.empty(count, dtype=np.byte)
    # 接收客户端 REQUEST 消息
    rec_req = comm.recv(rec_req, N)
    rec_req = pickle.loads(rec_req)
    print(
        f'INFO: Node [{rank}] receive [{rec_req.tag}] message from Node [{rec_req.i}] with the content 【{rec_req.o}】 and its sig is [{rec_req.sign}]')
    # 验证 REQUEST 消息
    if ser.check_rec(rec_req, signs, N):
        print(f'Node [{rank}] pass the verification of [{rec_req.tag}] from Node [{rec_req.i}]')
        print(f"-------------------Node [{ser.v}] is coming to PRE_PREPARE phase !!!-------------------")
        # 主节点发送 PRE-PREPARE 消息给各个节点
        if ser.v % N == rank:  # 判断主节点
            # 分配序号
            ser.n += 1
            # 计算消息摘要
            digest = hashlib.sha256(pickle.dumps(rec_req))
            digest = digest.hexdigest()
            # 生成 PRE-PREPARE 消息
            pre_prepare_msg = PRE_PREPARE(ser.v, ser.n, digest, ser.signature, rec_req)
            # 发送 PRE-PREPARE 消息
            for i in range(N):
                if i != ser.v % N:
                    send_pre_prepare_msg = pickle.dumps(pre_prepare_msg)
                    req = comm.send(send_pre_prepare_msg, i)
                    ser.history_rec_pre_prepare.append(pickle.loads(send_pre_prepare_msg))
    else:
        print(f'Node [{rank}] refuse the message [{rec_req.tag}] from Node [{rec_req.i}]')
    if rank != ser.v % N:
        # 动态分配内存
        status = MPI.Status()
        comm.Probe(source=ser.v % N, status=status)
        count = status.Get_count(MPI.BYTE)  # 获取接收到的整数个数
        rec_pre_prepare = np.empty(count, dtype=np.byte)
        # 接收 PRE-PREPARE 消息
        rec_pre_prepare = comm.recv(rec_pre_prepare, ser.v % N)
        rec_pre_prepare = pickle.loads(rec_pre_prepare)
        print(
            f'INFO: Node [{rank}] receive [{rec_pre_prepare.tag}] message from Node [{ser.v % N}] with the content 【{rec_pre_prepare.d}】 and its sig is [{rec_pre_prepare.sign}]')
        # 验证 PRE-PREPARE 消息
        if ser.check_rec(rec_pre_prepare, signs, N):
            print(f'Node [{rank}] pass the verification of [{rec_pre_prepare.tag}] from Node [{ser.v % N}]')
            print(f"-------------------Node [{ser.v}] is coming to PREPARE phase !!!-------------------")
            # 保存 Pre-Prepare 消息
            ser.history_rec_pre_prepare.append(rec_pre_prepare)
            # 生成 Prepare 消息
            prepare_msg = PREPARE(ser.v, rec_pre_prepare.n, rec_pre_prepare.d, ser.i, ser.signature)

            # 发送 PREPARE 消息
            for i in range(N):
                if i != rank:
                    req = comm.send(pickle.dumps(prepare_msg), i)
        else:
            print(f'Node [{rank}] refuse the message [{rec_pre_prepare.tag}] from Node [{ser.v % N}]')
    for i in range(N):
        if i != rank and i != ser.v % N:  # 主、副节点接收 PREPARE
            # 动态分配内存
            status = MPI.Status()
            comm.Probe(source=i, status=status)
            count = status.Get_count(MPI.BYTE)  # 获取接收到的整数个数
            rec_prepare = np.empty(count, dtype=np.byte)
            # 接收 PREPARE 消息
            rec_prepare = comm.recv(rec_prepare, source=i)
            rec_prepare = pickle.loads(rec_prepare)
            # 验证 PREPARE 消息
            if ser.check_rec(rec_prepare, signs, N):
                print(f'Node [{rank}] pass the verification of [{rec_prepare.tag}] from Node [{rec_prepare.i}]')
                ser.history_rec_prepare.append(rec_prepare)
            else:
                print(f'Node [{rank}] refuse the message [{rec_prepare.tag}] from Node [{rec_prepare.i}]')

    # 统计 PREPARE 消息
    if True:  # 查看是否 2f+1
        print(f"-------------------Node [{ser.v}] is coming to COMMIT phase !!!-------------------")
        # 生成 COMMIT 消息
        com_msg = COMMIT(ser.v, rec_prepare.n, rec_prepare.d, ser.i, ser.signature)
        # 发送 COMMIT 消息
        for i in range(N):
            if i != rank:
                req = comm.send(pickle.dumps(com_msg), i)

    for i in range(N):
        if i != rank:
            # 动态分配内存
            status = MPI.Status()
            comm.Probe(source=i, status=status)
            count = status.Get_count(MPI.BYTE)  # 获取接收到的整数个数
            rec_com = np.empty(count, dtype=np.byte)
            # 接受 COMMIT 消息
            rec_com = comm.recv(rec_com, i)
            rec_com = pickle.loads(rec_com)
            # 验证 COMMIT 消息
            if ser.check_rec(rec_com, signs, N):
                print(f'Node [{rank}] pass the verification of [{rec_com.tag}] from Node [{rec_com.i}]')
                ser.history_rec_commit.append(rec_com)
            else:
                print(f'Node [{rank}] refuse the message [{rec_com.tag}] from Node [{rec_com.i}]')

        # 统计 COMMIT 消息
        if True:  # 查看是否 2f+1
            print(f"-------------------Node [{ser.v}] is coming to REPLY phase !!!-------------------")
            # 生成 COMMIT 消息
            temp = ser.history_rec_pre_prepare[0].m
            rep_msg = REPLY(ser.v, temp.t, temp.i, ser.i, 'result', ser.signature)
            req = comm.send(pickle.dumps(rep_msg), temp.i)
            print("done")
# 释放共享窗口内存
win1.Free()
win2.Free()

# 确保所有进程都完成任务
comm.Barrier()
# 释放 MPI 资源
MPI.Finalize()
