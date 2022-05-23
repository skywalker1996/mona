import socket

addr = ("192.168.2.217", 8993)

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(addr)

while(True):
	print('')
	print('start recieve!!!')
	data = sock.recv(1024)
	print(data.decode())


# sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# sock.bind(addr)
# sock.listen(5)

# while(True):
# 	clisock, addr = sock.accept()
# 	print('连接成功！')
# 	data = clisock.recv(1024)
# 	print(data.decode())