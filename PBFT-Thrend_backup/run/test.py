import msgpack
from Message import *

REQUEST = {'tag': 'REQUEST',
                   'i': 0,
                   'signature': 0.219728347287,
                   'addr': ('127.0.0.1', 5000)
                   }
req_msg = msgpack.packb(REQUEST)
ss = msgpack.unpackb(req_msg)
print(req_msg)
print(ss)
