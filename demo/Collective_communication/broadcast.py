import mpi4py.MPI as MPI

'''
buf = comm.bcast(data_to_share, rank_of_root_process)

'''

comm = MPI.COMM_WORLD  # 通过命令行传入的参数np，调用MS-MPI获得一个通讯组，该通讯组定义了一组互相发消息的进程
comm_rank = comm.Get_rank()  # 为每一个进程分配一个rank
comm_size = comm.Get_size()  # 这组进程中共有comm_size个进程

print(f"comm_rank = {comm_rank}")  # 会被执行comm_size次，因为该程序在MPI中会被调用多次，完成进程间的通信
print(f"comm_size = {comm_size}")

if comm_rank == 0:
    data = [i for i in range(comm_size)]  # root进程初始化data_variable

data = comm.bcast(data if comm_rank == 0 else None, root=0)  # 为了发送消息，需要声明了一个广播
print("rank %d, got : " % comm_rank)
print(data)  # 接收进程通过data获得root节点广播的数据
