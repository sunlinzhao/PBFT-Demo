## PBFT共识算法的简单实现

### 01.角色设置

- 客户端
- 服务端（主/副节点）
- 消息类
- 日志类

### 02.实现操作

- 客户端

> 向主节点发送申请 <REQUEST,o,t,c>
>
>o：请求的具体操作，
>
>t：请求时客户端追加的时间戳，
>
>c：客户端标识。
>
>REQUEST：包含消息内容m，以及消息摘要d(m)。客户端对请求进行签名。

- 服务端（主节点）

> 1. 接收客户端的请求
>   
> 2. 处理客户端的请求
>
>   a. 校验消息
>
>           i. 接收到客户端的REQUEST消息后，检验请求消息摘要和签名是否正确
>
>           ii. 若不正确请丢弃，否则为其分配一个编号n,主要用于对客户端的请求进行排序
>   b.向所有节点广播 <PRE-PREPARE,v,n,d>
>          
>           v：视图编号，d客户端消息摘要，m消息内容。<PRE-PREPARE, v, n, d>进行主节点签名。
>           n：是要在某一个范围区间内的[h, H]。

- 服务端（副节点）

>   1 接收 PRE-PREPARE 消息
>
>   2 处理 PRE-PREPARE 消息
>       
>       a. 校验消息
>
>           i. 主节点签名是否正确
>           ii. d与m的摘要是否一致
>           iii. n是否在区间[h,H]内
>           iv. 是否已经收到了一条在同一v下的编号为n，但是签名不同的 PRE-PREPARE 消息
>       
>       非法要丢弃，否则向其他节点包括主节点发送 PREPARE 消息
>       
>   3 发送 <PREPARE, v, n, d, i> 消息给其他节点包括主节点
>   
>  ` v, n, d, m与上述PRE-PREPARE消息内容相同，i是当前副本节点编号`
>
>       a. <PREPARE, v, n, d, i>进行副本节点i的签名。
>
>       b. 记录 PRE-PREPARE和PREPARE 消息到 log 中，用于View Change过程中恢复未完成的请求操作
>
>   4 接收 PREPARE 消息
>
>   5 处理 PREPARE 消息
>   
>       a. 校验消息
>
>           i. 副本节点PREPARE消息签名是否正确
>           ii. 当前副本节点是否已经收到了同一视图v下的n
>           iii. n是否在区间[h, H]内
>           iv. d是否和当前已收到PRE-PPREPARE中的d相同
>       非法请求丢弃。如果副本节点i收到了2f+1个验证通过的PREPARE消息，则向其他节点包括主节点发送一条 COMMIT 消息
>
>    6 发送 <COMMIT, v, n, d, i> 消息
>
>   `v, n, d, i 与上述PREPARE消息内容相同`
>
>       i. <COMMIT, v, n, d, i>进行副本节点i的签名。
>       ii. 记录COMMIT消息到日志中，用于View Change过程中恢复未完成的请求操作。
>       iii. 记录其他副本节点发送的PREPARE消息到log中。
>
>    7 接受 COMMIT 消息
>    8 处理 COMMIT 消息
>
>       a. 校验消息
>
>           i. 副本节点COMMIT消息签名是否正确
>           ii. 当前副本节点是否已经收到了同一视图v下的n
>           iii. d与m的摘要是否一致
>           iv. n是否在区间[h, H]内
>
>       非法请求丢弃。如果副本节点i收到了2f+1个验证通过的COMMIT消息，说明当前网络中的大部分节点已经达成共识，运行客户端的请求操作o，并返回 REPLY给客户端
>
>   9 发送 <REPLY, v, t, c, i, r> 给客户端
>
>       r：是请求操作结果，客户端如果收到f+1个相同的REPLY消息，说明客户端发起的请求已经达成全网共识，否则客户端需要判断是否重新发送请求给主节点。记录其他副本节点发送的COMMIT消息到log中
>   10 广播 <VIEW-CHANGE,v+1,n,C,P,i> 给所有节点
>           
>       C：节点i保存的经过2f+1节点确认的state checkpoint消息的集合，确保视图变更前，已经stable checkpoint消息的安全
>       P：一个已经保存了n只够所有已经到达prepared状态消息的合集，确保试图变更前，已经prepared状态消息的安全
>   11 把旧视图中已经prepared的消息变为PRE-PREPARE然后重新广播，再次达到共识
>
>   12 新主节点收到 2f+1 VIEW-CHANGE 消息后，广播 <NEW-CHANGE,v+1,V,O> 消息
>
>       V：新主节点收到的（包括自己的）VIEW-CHANGE 消息集合
>       O：PRE-PREPARE 状态的消息集合，保证视图变更后 P 集合中的消息安全
>       新的的主节点计算 p = v mod |R| ;R=N
>       a. 校验签名和V和O是否合法，若验证通过则主副节点都进入试图v+1
>   
>


运行：`mpiexec -np 16 python PBFT-MPI\test_blocking.py`



