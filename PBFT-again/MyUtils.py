import socket

# 随机返回可用端口号
def get_free_port():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

# 根据节点总数 N 计算 PBFT 容错率
def calculate_tolerance(N):
    if (N-1) % 3 == 0:
        return int((N-1) / 3)
    elif (N-1) % 3 == 1:
        return int((N-2) / 3)
    elif (N-1) % 3 == 2:
        return int(((N-3) / 3) + 1)
    else:
        return None