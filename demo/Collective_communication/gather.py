import mpi4py.MPI as MPI
import numpy as np

'''
recvbuf = comm.gather(sendbuf, rank_of_root_process)
'''

comm = MPI.COMM_WORLD  # 通过命令行传入的参数np，调用MS-MPI获得一个通讯组，该通讯组定义了一组互相发消息的进程
comm_rank = comm.Get_rank()  # 为每一个进程分配一个rank
comm_size = comm.Get_size()  # 这组进程中共有comm_size个进程

if comm_rank == 0:
    data = np.random.rand(comm_size, 2)
    print(data)
else:
    data = None

local_data = comm.scatter(data, root=0)  # root将raw数据散播到每个进程中，等待进程返回处理结果
if (comm_rank % 2 == 0):  # 偶数进程将local_data置为-local_data
    local_data = -local_data  # 对数据进行处理
else:  # 奇数进程将local_data置为0
    local_data = 0  # 对数据进行处理
print("rank %d got data and finished dealing." % comm_rank)
print(local_data)  # 接收进程通过local_data获得root节点散播的数据

# 由root=0进行数据的收集
# 因为需要进行收集工作，所以是最后执行完的。
combine_data = comm.gather(local_data, root=0)  # 数据处理完毕，该进程将结果发送给root
if comm_rank == 0:
    print(f"rank {comm_rank} gather data : {combine_data}")
