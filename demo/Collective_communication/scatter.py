import mpi4py.MPI as MPI
import numpy as np

'''
recvbuf  = comm.scatter(sendbuf, rank_of_root_process)
'''

comm = MPI.COMM_WORLD  # 通过命令行传入的参数np，调用MS-MPI获得一个通讯组，该通讯组定义了一组互相发消息的进程
comm_rank = comm.Get_rank()  # 为每一个进程分配一个rank
comm_size = comm.Get_size()  # 这组进程中共有comm_size个进程

if comm_rank == 0:
    # 一定要确保data的长度是np的数量
    data = np.random.rand(comm_size, 3)
    # data = [i for i in range(comm_size)]
    # data = [[1], [2], [3], [4]]
    print("all data by rank %d : " % comm_rank)
    print(data)
else:
    data = None

local_data = comm.scatter(data, root=0)
print("rank %d, got : " % comm_rank)
print(local_data)  # 接收进程通过local_data获得root节点散播的数据
