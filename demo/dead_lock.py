from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.rank  # 通过命令行传入的参数np，调用MS-MPI获得一个通讯组，该通讯组定义了一组互相发消息的进程
print("my rank is : ", rank)  # 为每一个进程分配一个rank

'''必定会产生死锁'''
if rank == 1:
    data_send = "a"
    destination_process = 5
    source_process = 5
    data_received = comm.recv(source=source_process)  # 进程1阻塞，等待接收进程5发送的资源
    comm.send(data_send, dest=destination_process)  # 进程1接收到5发送的资源后，向进程5发送资源
    print("sending data %s " % data_send + "to process %d" % destination_process)
    print("data received is = %s" % data_received)

if rank == 5:
    data_send = "b"
    destination_process = 1
    source_process = 1
    data_received = comm.recv(source=source_process)  # 进程5阻塞，等待接收进程1发送的资源
    comm.send(data_send, dest=destination_process)  # 进程5接收到1发送的资源后，向进程1发送资源
    print("sending data %s :" % data_send + "to process %d" % destination_process)
    print("data received is = %s" % data_received)
