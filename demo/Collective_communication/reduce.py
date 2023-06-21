import mpi4py.MPI as MPI
import numpy as np

'''
comm.Reduce(senddata, recvdata, root=0, op=MPI.SUM)
'''

comm = MPI.COMM_WORLD  # 通过命令行传入的参数np，调用MS-MPI获得一个通讯组，该通讯组定义了一组互相发消息的进程
comm_rank = comm.Get_rank()  # 为每一个进程分配一个rank
comm_size = comm.Get_size()  # 这组进程中共有comm_size个进程

if comm_rank == 0:
    data = np.random.randint(low=0, high=10, size=(comm_size, 3))
    print(data)
else:
    data = None

local_data = comm.scatter(data, root=0)  # root将raw数据散播到每个进程中，等待进程返回处理结果
print(f"rank {comm_rank} recieve data : {local_data}")  # 接收进程通过local_data获得root节点散播的数据

# 和gather相同，由root=0进行数据的规约
all_sum = comm.reduce(local_data, op=MPI.SUM, root=0)  # 数据处理完毕，该进程将结果发送给root
if comm_rank == 0:
    print(f"rank {comm_rank} reduce data : {all_sum}")
