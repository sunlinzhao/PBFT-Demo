from mpi4py import MPI

'''
拓扑是 MPI 提供的一个有趣功能。
如前所述，所有通信功能（点对点或集体）都是指一组进程。
我们一直使用包含所有进程的 MPI_COMM_WORLD 组。它为大小为n的通信组的每个进程分配 0 - n-1 的一个rank。
但是，MPI允许我们为通信器分配虚拟拓扑。它为不同的进程定义了特定的标签分配。这种机制可以提高执行性能。
实际上，如果构建虚拟拓扑，那么每个节点将只与其虚拟邻居进行通信，从而优化性能。

例如，如果rank是随机分配的，则消息可能会在到达目的地之前被迫传递给许多其他节点。
除了性能问题之外，虚拟拓扑还可确保代码更清晰可读。 MPI提供两种建筑拓扑。
第一个构造创建笛卡尔拓扑，而后者可以创建任何类型的拓扑。具体来说，在第二种情况下，我们必须提供要构建的图形的邻接矩阵。
我们将只处理笛卡尔拓扑，通过它可以构建多种广泛使用的结构：网格，环形等等。用于创建笛卡尔拓扑的函数如下所示：

comm.Create_cart((number_of_rows,number_of_columns))

'''

from mpi4py import MPI
import numpy as np

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3
neighbour_processes = [0, 0, 0, 0]  # 上，下，左，右

# 利用笛卡尔坐标系绘制进程间的拓扑结构M x N，可以绘制2D和3D
# 参考 https://learn2codewithmesite.wordpress.com/2017/10/16/creating-topologies-in-mpi4py/， https://wgropp.cs.illinois.edu/courses/cs598-s15/lectures/lecture28.pdf
if __name__ == "__main__":
    comm = MPI.COMM_WORLD  # 通过命令行，获取通讯组
    rank = comm.rank  # 获取当前进程的rank
    size = comm.size  # 获取通讯组中进程的个数

    print(f"comm_rank = {rank}")  # 会被执行comm_size次，因为该程序在MPI中会被调用多次，完成进程间的通信
    print(f"comm_size = {size}")

    grid_rows = int(np.floor(np.sqrt(comm.size)))
    grid_column = comm.size // grid_rows
    # 最后的拓扑是 2x2 的网状结构，大小为4，和进程数一样：
    if grid_rows * grid_column > size:
        grid_column -= 1
    if grid_rows * grid_column > size:
        grid_rows -= 1
    if (rank == 0):
        print("Building a %d x %d grid topology:" % (grid_rows, grid_column))

    # cartesian_communicator = comm.Create_cart( (grid_rows, grid_column), periods=(True, True), reorder=True)  #为通讯器建立笛卡尔虚拟拓扑
    cartesian_communicator = comm.Create_cart((grid_rows, grid_column), periods=(False, False),
                                              reorder=True)  # 为通讯器建立笛卡尔虚拟拓扑, Return type: Cacomm

    my_mpi_row, my_mpi_col = cartesian_communicator.Get_coords(
        cartesian_communicator.rank)  # 通过 Get_coords() 方法，可以确定一个进程横纵坐标

    # ‘Shift’ allows us to know the rank of processes that are neighbours of a given process in a particular direction
    neighbour_processes[UP], neighbour_processes[DOWN] = cartesian_communicator.Shift(direction=0,
                                                                                      disp=1)  # direction = 0表上下
    neighbour_processes[LEFT], neighbour_processes[RIGHT] = cartesian_communicator.Shift(direction=1,
                                                                                         disp=1)  # direction = 1表左右

    print(
        "Process = %s row = %s column = %s ----> neighbour_processes[UP] = %s neighbour_processes[DOWN] = %s neighbour_processes[LEFT] =%s neighbour_processes[RIGHT]=%s" % (
            rank, my_mpi_row, my_mpi_col, neighbour_processes[UP],
            neighbour_processes[DOWN], neighbour_processes[LEFT],
            neighbour_processes[RIGHT]))


# mpiexec -n 4 python demo\topology.py