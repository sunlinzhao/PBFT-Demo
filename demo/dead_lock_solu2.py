from mpi4py import MPI

'''

在mpi4py中，有一个特定的函数统一了向一特定进程发消息和从一特定进程接收消息的功能，叫做 Sendrecv
Sendrecv(self, sendbuf, int dest=0, int sendtag=0, recvbuf=None, int source=0, int recvtag=0, Status status=None)

'''

comm = MPI.COMM_WORLD
rank = comm.rank  # 通过命令行传入的参数np，调用MS-MPI获得一个通讯组，该通讯组定义了一组互相发消息的进程
print("my rank is : ", rank)  # 为每一个进程分配一个rank

'''使用 sendrecv 函数'''
if rank == 1:
    data_send = "a"
    destination_process = 5
    source_process = 5
    data_received = comm.sendrecv(data_send, dest=destination_process,
                                  source=source_process)  # 该函数函数统一了向一特定进程发消息和从一特定进程接收消息的功能
    print(f"rank = {rank}, data received is = {data_received}")
if rank == 5:
    data_send = "b"
    destination_process = 1
    source_process = 1
    data_received = comm.sendrecv(data_send, dest=destination_process, source=source_process)
    print("data received is = %s" % data_received)
    print(f"rank = {rank}, data received is = {data_received}")
