import socket

addr = ("192.168.2.217", 8993)
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.sendto('hello world'.encode(), addr)

# sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# sock.connect(addr)
# sock.send('hello world'.encode())
# print('send successfully!')