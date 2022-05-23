

import os.path as osp 
import time


# start = time.time()

# a = int((time.time()%10**3) * 1000000)
# b = int((time.time()%10**20) * 1000000)
# c = int((time.time()%(10**3))*1000000) 

# print(a)
# print(b)
# print(c)

# print("---",time.time())
# this_dir = osp.abspath(osp.dirname(osp.dirname(__file__)))
# print(this_dir)

# a = 0.02
# print(float(a))

# a = 123
# b = 456
# c = 789

# res = b''
# res += a.to_bytes(4, byteorder="big")
# res += b.to_bytes(4, byteorder="big")
# res += c.to_bytes(4, byteorder="big")


# res_a = bytearray(res)
# print(type(res))
# print(type(res_a))

# print(int.from_bytes(res[0:4], byteorder="big"))
# print(int.from_bytes(res[4:8], byteorder="big"))
# print(int.from_bytes(res[8:12], byteorder="big"))
# print()
# print(int.from_bytes(res_a[0:4], byteorder="big"))
# print(int.from_bytes(res_a[4:8], byteorder="big"))
# print(int.from_bytes(res_a[8:12], byteorder="big"))

# a = {}
# a['name'] = 'henry'
# a['age'] = 20

a = [0,0,0,0,0,0,1,2,3,4,5]
print([a[i] for i in range(len(a)) if a[i]>0])
print(max(a))
