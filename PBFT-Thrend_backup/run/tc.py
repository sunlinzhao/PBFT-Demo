# 客户端
from socket import *

# 主机地址为 '0.0.0.0',表示绑定本机所有网络接口IP地址，否则绑定一个
# 等待客户端连接
IP = '127.0.0.1'
SERVER_PORT = 50003
BUFLEN = 512


# 实例化一个 socket 对象，指明协议
dataSocket = socket(AF_INET, SOCK_STREAM)

# 链接服务端 socket
dataSocket.connect((IP,SERVER_PORT))

while True:
    # 从终端读入用户输入的字符串
    toSend = input('>>> ')
    if toSend =='exit':
        break
    # 发送消息也要编码为 bytes
    dataSocket.send(toSend.encode())

    # 等待接收服务端消息，阻塞方式
    recved = dataSocket.recv(BUFLEN)
    # 如果返回空bytes，表示对方关闭了连接
    if not recved:
        break
    # 打印读取的信息
    print(recved.decode())
    # 发送数据类型必须是bytes，所以要编码、
    dataSocket.send(f'服务端接收到了信息{info}'.encode())

dataSocket.close()
