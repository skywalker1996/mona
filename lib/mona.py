import time
from queue import Queue  
import numpy 
import socket
import cv2
from threading import Thread, Lock
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import sys 
import os.path as osp
sys.path.append(osp.abspath(osp.dirname(osp.dirname(__file__))))
from lib.packet_utils import PiecePack, PacketLossTracker
from configs.config import Config
import copy
import datetime
#import rate control module
from lib.rate_control import rate_control_module
from lib.monitorFlux import MonitorFlux

class mona(object):

	def __init__(self, type):
		self.type = type

	def Server(self, configs):

		self.config = Config('cfg_mona.conf')

		#率控制相关
		#delay between sending a full frame 
		self.server_sending_delay = float(self.config.get('server', 'initial_sending_delay'))
		self.server_sending_delay_min = float(self.config.get('server', 'sending_delay_min'))
		self.server_sending_delay_max = float(self.config.get('server', 'sending_delay_max'))
		self.monitor_interval = int(self.config.get('server', 'monitor_interval'))

		self.recv_queue_size = int(self.config.get("server", "recv_queue_size"))
		self.send_queue_size = int(self.config.get("server", "send_queue_size"))

		#split one frame into several pieces
		self.frame_pieces = int(self.config.get('global', 'frame_pieces'))

		#the monitor recording window
		self.record_window = int(self.config.get('global', 'record_window'))

		#RTT
		self.network_delay = 0
		self.packet_loss = 0

		self.server_address = configs['server_address']
		self.client_address = configs['client_address']
		self.ack_address = configs['ack_address']

		self.w = configs['w']
		self.h = configs['h']
		self.d = configs['d']
		self.frame_total_size = self.w*self.h*self.d

		self.server_send_buffer = Queue(self.send_queue_size)
		self.server_recv_buffer = Queue(self.recv_queue_size)

		self.time_recorder = {}
		self.frame_id = 0

		self.sending_fps = 0

		self.encode_param=[int(cv2.IMWRITE_JPEG_QUALITY), configs["encode_param"]]

		#monitor
		self.monitor_ready = False

		self.network_delay_record = [0] * self.record_window    #单位ms
		self.packet_loss_record = [0] * self.record_window
		self.send_buffer_record = [0] * self.record_window
		self.recv_buffer_record = [0] * self.record_window
		self.send_queue_delay_record = [0] * self.record_window  #单位ms
		self.server_sending_delay_record = [0] * self.record_window #单位ms
		self.record_count = 0
		self.queue_monitor_count = 0

		self.send_queue_delay = 0

		#每一帧切分后放进piece_array
		self.piece_array = []
		for i in range(self.frame_pieces):
			self.piece_array.append(None)

		self.frame = numpy.zeros(self.frame_total_size, dtype=numpy.uint8)

		self.init_frame_send_connection()

		#发送线程
		self.frame_sending_thread = Thread(target=self.frame_sending_module, args=())
		self.frame_sending_thread.daemon = True


		#接收ACK线程
		self.ack_recv_thread = Thread(target=self.ack_recv_thread, args=())
		self.ack_recv_thread.daemon = True
		

		#接收控制信息线程
		self.control_recv_thread = Thread(target=self.control_recv_thread, args=())
		self.control_recv_thread.daemon = True
		


		global_config = Config('global.conf')

		self.measurement = global_config.get('database', 'measurement')

		db_para = {}
		db_para['url'] = global_config.get('database', 'url')
		db_para['token'] = global_config.get('database', 'token')
		db_para['org'] = global_config.get('database', 'org')
		db_para['bucket'] = global_config.get('database', 'bucket')

		self.Monitor = MonitorFlux(db_para=db_para, 
								   plot_number=5, 
								   monitor_targets=None)

		self.ax_list = {}
		self.line_list = {}

		self.frame_sending_thread.start()
		self.ack_recv_thread.start()
		self.control_recv_thread.start()
		# self.monitor.start()

		self.RL_Module = rate_control_module(self.server_sending_delay)

		print('init successfully')
		return self

	#frame发送控制模块
	def frame_sending_module(self):
		time_counter = 0
		frame_counter = 0
		while(True):
			if(frame_counter%10==0):
				if(frame_counter!=0):
					time_delta = time.time() - time_counter 
					self.sending_fps = int(10.0/time_delta) if time_delta!=0 else 0
				time_counter = time.time()
				frame_counter = 0

			piece_array = self.server_send_buffer.get()
			for i in range(len(piece_array)):
				#modidy the create_time to the send time
				create_time = int.from_bytes(piece_array[i][22:30], byteorder="big")
				send_time = int((time.time()%(10**3))*1000000) 
				self.send_queue_delay = (send_time - create_time)/1000.0
				self.send_queue_delay_record = self.send_queue_delay_record[1:]+[self.send_queue_delay]
				piece_array[i][22:30] = send_time.to_bytes(8, byteorder="big")
				# if(sys.getsizeof(piece_array[i])>1500):
					# print('piece id {}, the size is {} bytes'.format(i, sys.getsizeof(piece_array[i])))
				self.sock.sendto(piece_array[i], self.client_address)
				# self.sock.sendto(piece_array[i], ("192.168.2.182", 9995))

				#率控制的控制目标
			time.sleep(self.server_sending_delay)
			frame_counter+=1


	def init_frame_send_connection(self):
		try:
			self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			# self.sock.bind(self.address)
		except socket.error as msg:
			print(msg)
			sys.exit(1)

	def send_frame(self, frame_raw):
		# print(frame_raw.shape)
		threads = []
	
		for i in range(self.frame_pieces):
			thread = self.pack_frame(self.frame_id, i, frame_raw, self.piece_array)
			threads.append(thread)

		#等待所有线程都结束
		for t in threads:
			t.join()
		#添加到发送队列
		# print(self.piece_array)
		self.server_send_buffer.put(copy.copy(self.piece_array))
		self.frame_id += 1
		# print('the send buffer size is: ', self.server_send_buffer.qsize())


	def pack_frame(self, frame_id, piece_id, data, piece_array):
       
		if len(data) == 0:
		    return None
		# intialize compress thread
		# print('packing data piece #',index)
		thread = Thread(target=self.compress, args=(frame_id, piece_id, data, piece_array))
		thread.daemon = True
		thread.start()

		return thread

	def compress(self, frame_id, piece_id, frame_raw, piece_array):
		if len(frame_raw) == 0: return
		idx_frame = int(frame_raw.shape[0]/self.frame_pieces)
		# 分片下标计算
		row_start = piece_id* idx_frame
		row_end = (piece_id+1)* idx_frame
		# 视频分片压缩，idx对应当前分片的序号
		result, imgencode = cv2.imencode('.jpg', frame_raw[row_start:row_end], self.encode_param)
		# if(sys.getsizeof(imgencode)>1500):
		# 	print('piece id {}, the size is {}'.format(piece_id, sys.getsizeof(imgencode)))
		if result:
		    imgbytes = imgencode.tobytes()
		    data_len = len(imgbytes)
		    create_time = int((time.time()%(10**3))*1000000) 
		    res = self.pack_frame_head(data_len, frame_id, piece_id, create_time)
		    res += imgbytes 

		    # 更新
		    piece_array[piece_id] = res
		
		return 1

	#接收ACK信号
	def ack_recv_thread(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(self.ack_address)
		# s.bind(("192.168.2.217", 8993))

		while True:
			# print('start receive acks!')
			data = s.recv(128)
			# print('get the ack packet')
			if len(data) > 0:
				ack = json.loads(data.decode())
				loss = ack['packet_loss']
				ctime = ack['create_time']
				f_id = ack['frame_id']
				now = int((time.time()%(10**3))*1000000) #ns
				# print("ctime: {}, and now: {}".format(ctime, now))
				self.network_delay = round(((now - ctime)/1000.0),3)  #RTT (ms)
				self.packet_loss = loss
				self.record_count += 1
				# self.server_sending_delay += 0.0001
				#add to the records list
				# print("network_delay: {}, ack_frame: {}, current_frame: {}".format(self.network_delay, f_id, self.frame_id))
				
				self.network_delay_record = self.network_delay_record[1:]+[self.network_delay]
				self.packet_loss_record = self.packet_loss_record[1:]+[self.packet_loss]

				if(self.record_count>11):
					server_sending_delay, utility = self.RL_Module.action({'network_delay': self.network_delay_record[-10:],
															  'packet_loss': self.packet_loss_record[-10:],
															  'send_queue_delay': self.send_queue_delay_record[-10:]})
					if(utility==None):
						utility = 0.1

				else:
					utility = 0.1

				data = self.construct_data(self.network_delay, self.packet_loss, self.send_queue_delay, self.server_recv_buffer.qsize(), self.server_sending_delay, utility)
				self.Monitor.pushData(measurement = self.measurement, datapoints = [data], tags = {'version':'0.1'} )
		s.close()

	#控制信息接收线程
	def control_recv_thread(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(self.server_address)

		while True:
			data = s.recv(128)
			if len(data) > 0:
				data = json.loads(data.decode())
				self.server_recv_buffer.put(data)
		s.close()

	def get_sending_status(self):
		return self.network_delay, self.packet_loss

	def get_control_message(self):
		return self.server_recv_buffer.get()

	def control_msg_buffer_is_empty(self):
		return self.server_recv_buffer.empty()

	def Client(self, configs):

		self.config = Config('cfg_mona.conf')
		#用户控制信息发送率参数
		self.client_sending_delay = float(self.config.get('client', 'initial_sending_delay'))
		self.client_sending_delay_min = float(self.config.get('client', 'sending_delay_min'))
		self.client_sending_delay_max = float(self.config.get('client', 'sending_delay_max'))

		self.recv_queue_size = int(self.config.get("client", "recv_queue_size"))
		self.send_queue_size = int(self.config.get("client", "img_queue_size"))
		self.img_queue_size = int(self.config.get('client', 'send_queue_size'))
		self.frame_pieces = int(self.config.get('global', 'frame_pieces'))

		self.network_delay = 0
		self.packet_loss = 0

		self.server_address = configs['server_address']
		self.client_address = configs['client_address']
		self.ack_address = configs['ack_address']


		self.w = configs['w']
		self.h = configs['h']
		self.d = configs['d']
		self.frame_total_size = self.w*self.h*self.d

		self.encode_param=[int(cv2.IMWRITE_JPEG_QUALITY), configs["encode_param"]]

		self.client_recv_buffer = Queue(maxsize=self.recv_queue_size )
		self.img_buffer = Queue(maxsize=self.img_queue_size)
		self.client_send_buffer = Queue(32)

		self.control_id = 0
		self.piece_array = []
		for i in range(self.frame_pieces):
			self.piece_array.append(None)

		self.last_frame_id = 0
		self.ack_period_count = 0
		self.startFlag = 1

		#只计算过去100帧中的丢包率
		self.Loss_log_period = int(self.config.get('client', 'Loss_log_period'))
		self.loss_tracker = PacketLossTracker(self.frame_pieces, self.Loss_log_period)

		#接受线程x
		self.client_recv_thread = Thread(target=self.client_recv_thread, args=())
		self.client_recv_thread.daemon = True
		

		#rebuild线程，根据收到的piece重建完整的frame
		self.client_rebuild_thread = Thread(target=self.client_rebuild_thread, args=())
		self.client_rebuild_thread.daemon = True


		self.control_sending_module = Thread(target=self.control_sending_module, args=())
		self.control_sending_module.daemon = True
		

		self.client_recv_thread.start()
		self.client_rebuild_thread.start()
		self.control_sending_module.start()

		return self

	def init_recv_connection(self):
		try:
			sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			rcv_size = 1024*1024
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,rcv_size);
			sock.bind(self.client_address)
			return sock
		except socket.error as msg:
			print(msg)
			sys.exit(1)


	def client_recv_thread(self):
		sock = self.init_recv_connection()
		# print('the recv buffer size is {}'.format(sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)))
		stopped = False
		last_time = int(time.time()*1000)
		while True:
			if stopped: break
			# otherwise, ensure the queue has room in it
			# print('the recv_buffer size is {}'.format(self.client_recv_buffer.qsize()))
			if not self.client_recv_buffer.full():
				try:
					# print('')
					# print('start recieve!!!')
					now = int(time.time()*1000)
					# print('recieve time delta: ', now - last_time)
					data, addr = sock.recvfrom(60000)
					# print('get the data!!!')
					last_time = now
					# print('recieve data size:', len(data))
					frame_id, piece_id, ctime, raw_img = self.unpack_frame(data)
					# print('frame id: {} and piece id: {}'.format(frame_id, piece_id))

					# add the frame to the queue
					# print('receive data pack frame id: {} and piece id: {}'.format(frame_id, piece_id))
					self.client_recv_buffer.put(PiecePack(frame_id, piece_id, ctime, raw_img))
					# print('the size of imgQ is: ', self.client_recv_buffer.qsize())
				except:
					print('exception caused by recv thread!')
					pass

			else:
				time.sleep(0.01)  # Rest for 10ms, we have a full queue
				# print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

	def client_rebuild_thread(self):

		frame_mark = {}
		frame_buffer = {}
		ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		ack_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  
		while True:

			pack = self.client_recv_buffer.get()
			frame_id = pack.frame_id
			piece_id = pack.piece_id
			# print('Frame id: {}, Piece id: {}'.format(frame_id, piece_id))

			#判断是否是新开，若是则更新last_frame_id来支持续传
			if(self.startFlag==1):
				self.last_frame_id = frame_id
				self.startFlag = 0
			else:
				#检查包的frame id是否过期   ，若过期了就丢弃
				if(frame_id<self.last_frame_id):
					# print('get expired Frame id: {}, Piece id: {}'.format(frame_id, piece_id))
					continue


			raw_img = pack.piece
			data = numpy.frombuffer(raw_img, dtype=numpy.uint8)
			line_img = cv2.imdecode(data, cv2.IMREAD_COLOR).flatten()
			# print('data size: ', len(data))
 
			if frame_id in frame_mark:
				frame_mark[frame_id] += 1
			else:
				frame_mark[frame_id] = 1
				frame_buffer[frame_id] = numpy.zeros(self.frame_total_size, dtype=numpy.uint8)

			# print('rebuild peice ',idx)
			time_mark = pack.ctime
			# avg_time += ctime


			row_start = piece_id * len(line_img)
			row_end = (piece_id+1) * len(line_img)
			frame_buffer[frame_id][row_start:row_end] = line_img
			# print('get the packet for frame {} and piece {}.'.format(frame_id, piece_id))
			#收到完整的一帧
			if(frame_mark[frame_id]==self.frame_pieces):
				self.last_frame_id = frame_id
				# print('get one full frame #', frame_id)
				self.img_buffer.put(frame_buffer[frame_id].reshape(self.h, self.w, self.d))

				# self.loss_tracker.update_log(frame_mark[frame_id])
				frame_mark.pop(frame_id)
				frame_buffer.pop(frame_id)
				self.ack_period_count += 1

				# print('ack_period_count = ', self.ack_period_count)

			#每隔Loss_log_period进行一次loss计算
			if(self.ack_period_count>=self.Loss_log_period):
				self.loss_tracker.clear()
				self.ack_period_count = 0
				# 清除过期帧
				keys = list(frame_mark.keys())
				for key in keys:
					if(key<frame_id):
						# print("********************* frame {} only get {} pieces!!".format(key, frame_mark[key]))
						self.loss_tracker.update_log(frame_mark[key])
						frame_mark.pop(key)
						frame_buffer.pop(key)

				# print('send the ack packet to the server:', self.ack_address)
				self.info_pack = self.pack_client_ack_data(self.loss_tracker.get_current_loss(), time_mark, frame_id)
				# print('send the ack packet to the server:', self.ack_address)
				ack_socket.sendto(self.info_pack, self.ack_address)
		return

	def control_sending_module(self):

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		while True:

			time.sleep(self.client_sending_delay)
			if self.client_send_buffer.empty(): continue
			s.sendto(self.client_send_buffer.get().encode(), self.server_address)
			pass
		s.close()
		return


	def send_control_message(self, mess):
		self.client_send_buffer.put(mess)
		return

	def get_recv_img(self):

		if self.img_buffer.qsize() == 0:
			return None
		frame = self.img_buffer.get()

		return frame

	# pack the client ack packet
	def pack_client_ack_data(self, loss, ctime, frame_id):
		res = {}
		res['type'] = 'ack'
		res['packet_loss'] = loss
		res['create_time'] = ctime
		res['frame_id'] = frame_id
		res = json.dumps(res)
		return res.encode()



	def close_connection(self):
		self.sock.close()



	def pack_frame_head(self, data_len, frame_id, piece_id, create_time):

		res = b''
		res += "frame".encode()
		res += data_len.to_bytes(4, byteorder="big")
		res += frame_id.to_bytes(12, byteorder="big")
		res += piece_id.to_bytes(1, byteorder="big")
		res += create_time.to_bytes(8, byteorder="big")
		# print('pack frame id: {}, piece id： {}'.format(frame_id, piece_id))
		return bytearray(res)

	def unpack_frame_header(self, head_block):
		name = head_block[:4]
		data_len = int.from_bytes(head_block[5:9], byteorder='big')
		frame_id = int.from_bytes(head_block[9:21], byteorder='big')
		piece_id = int.from_bytes(head_block[21:22], byteorder='big')
		create_time = int.from_bytes(head_block[22:30], byteorder='big')
		# print('unpack frame id: {}, piece id： {}'.format(frame_id, piece_id))
		return name, data_len, frame_id, piece_id, create_time

	def unpack_frame(self, res):
		# print('unpack data!!!!')
		data_len=0
		index=-1
		create_time=0
		data=b''

		head_block = res[:30]
		name, data_len, frame_id, piece_id, create_time = self.unpack_frame_header(head_block)
		body_block = res[30:]
		# print('finish unpacking!!!')
		return frame_id, piece_id, create_time, body_block

	def construct_data(self,network_delay, packet_loss, sending_queue_delay, recv_buffer_size, server_sending_delay, utility ):

		data = {}

		data['network_delay'] = network_delay
		data['packet_loss'] = packet_loss
		data['sending_queue_delay'] = sending_queue_delay
		data['recv_buffer_size'] = recv_buffer_size
		data['server_sending_delay'] = server_sending_delay
		data['utility'] = utility
		data['time'] = datetime.datetime.utcnow().isoformat()

		# for key in data:
		# 	if(data[key]==None):
		# 		print("@@@@@@@@@@@ get None value of {}".format(key))

		return data







