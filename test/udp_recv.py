import socket

def init_recv_connection():
	try:
		sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(("192.168.2.217", 8993))
		return sock
	except socket.error as msg:
		print(msg)
		sys.exit(1)

def unpack_frame(res):
	# print('unpack data!!!!')
	data_len=0
	index=-1
	create_time=0
	data=b''

	head_block = res[:30]
	name, data_len, frame_id, piece_id, create_time = unpack_frame_header(head_block)
	body_block = res[30:]
	# print('finish unpacking!!!')
	return frame_id, piece_id, create_time, body_block

def unpack_frame_header(head_block):
	name = head_block[:4]
	data_len = int.from_bytes(head_block[5:9], byteorder='big')
	frame_id = int.from_bytes(head_block[9:21], byteorder='big')
	piece_id = int.from_bytes(head_block[21:22], byteorder='big')
	create_time = int.from_bytes(head_block[22:30], byteorder='big')
	# print('unpack frame id: {}, piece id： {}'.format(frame_id, piece_id))
	return name, data_len, frame_id, piece_id, create_time


sock = init_recv_connection()
piece_id_buf = 0

frame_mark = {}
check_period = 100
packet_count = 0

while(True):
	print('start recieve!!!')
	data, addr = sock.recvfrom(60000)
	# print('recieve data size:', len(data))
	frame_id, piece_id, ctime, raw_img = unpack_frame(data)

	if frame_id in frame_mark:
		frame_mark[frame_id] += 1
		if(frame_mark[frame_id]==10):
			frame_mark.pop(frame_id)
			# print("frame {} get!!".format(frame_id))

	else:
		frame_mark[frame_id] = 1
	packet_count += 1

	if(packet_count==check_period):
		packet_count = 0
		keys = list(frame_mark.keys())
		for key in keys:
			if(key < frame_id):
				# print("********************* frame {} only get {} pieces!!".format(key, frame_mark[key]))
				frame_mark.pop(key)

	print('recv packet for Frame {} and piece {}'.format(frame_id, piece_id))
