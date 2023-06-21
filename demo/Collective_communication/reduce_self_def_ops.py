import mpi4py.MPI as MPI
import numpy as np


# 自定义op --- 自定义算子
def my_func(a, b):
    f = a * a + b * b
    return f


comm = MPI.COMM_WORLD
comm_rank = comm.Get_rank()
comm_size = comm.Get_size()

if comm_rank == 0:
    data = np.random.rand(comm_size, 1)
    print(data)
else:
    data = None

local_data = comm.scatter(data, root=0)
local_data = -local_data  # 对数据进行处理
print("rank %d got data and finished dealing." % comm_rank)
print(local_data)

all_sum = comm.reduce(local_data, root=0, op=my_func)
if comm_rank == 0:
    print("sum is :", all_sum)
