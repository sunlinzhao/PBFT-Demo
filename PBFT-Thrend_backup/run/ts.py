# 服务端
from socket import *

# 主机地址为 '0.0.0.0',表示绑定本机所有网络接口IP地址，否则绑定一个
# 等待客户端连接
IP = '127.0.0.1'
# 端口号
PORT = 50003
# 定义一次从socket缓冲区最多读入512个字节数据
BUFLEN = 512

# 实例化一个socket对象
# 参数 AF_INET 表示该socket网络层使用IP协议
# 参数 SOCK_STREAM 表示socket传输层使用tcp协议

listenSocket = socket(AF_INET, SOCK_STREAM)

# socket 绑定地址和端口
listenSocket.bind((IP, PORT))

# 使得Socket处于监听状态，等待客户端连接请求
# 参数 5 表示，最多接受多少个等待连接的客户端
listenSocket.listen(5)
print(f'服务端启动成功, 在{PORT}端口等待客户端连接...')

# 返回的 dataSocket 用来通信、传输数据
dataSocket, addr = listenSocket.accept()
print('接受一个客户端连接:', addr)

while True:
    # 尝试读取对方发送的消息
    # BUFLEN 指定从接收缓冲里最多读取多少字节。阻塞方式
    recved = dataSocket.recv(BUFLEN)
    # 如果返回空bytes，表示对方关闭了连接
    # 退出循环，结束消息收发
    if not recved:
        break
    # 读取数据类型是bytes，需要解码为字符串
    info = recved.decode()
    print(f'收到对方信息：{info}')

    # 发送数据类型必须是bytes，所以要编码、
    dataSocket.send(f'服务端接收到了信息{info}'.encode())


# 服务端也调用close()关闭socket
dataSocket.close()
listenSocket.close()

# 查看端口号使用状态: netstat -an|find /i "50000"
# 关闭端口号 进程： Tasklist | findstr /i TIME_WAIT
# netstat -ano | findstr :50000