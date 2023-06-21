# 需要将这段代码保存成文件才能实现多进程程序的运行
import mpi4py.MPI as MPI

comm = MPI.COMM_WORLD  # 通过命令行传入的参数np，调用MS-MPI获得一个通讯组，该通讯组定义了一组互相发消息的进程
comm_rank = comm.Get_rank()  # 为每一个进程分配一个rank
comm_size = comm.Get_size()  # 这组进程中共有comm_size个进程

print(f"comm_rank = {comm_rank}")  # 会被执行comm_size次，因为该程序在MPI中会被调用多次，完成进程间的通信
print(f"comm_size = {comm_size}")

data_send = [comm_rank] * 4
comm.send(data_send, dest=(comm_rank + 1) % comm_size)  # 进程i会给进程 (i+1) % size发消息 （循环队列）
# 如果comm_rank-1<0,会自动加comm_size变为正数
data_recv = comm.recv(source=(comm_rank - 1) % comm_size)  # 进程i会接收进程(i - 1) % size发过来的消息（循环队列）
print("my rank is %d, I received :" % comm_rank)
print(data_recv)
