from threading import Thread, Lock
import socket
import cv2
import numpy
import time
import sys
import os
from config import Config
import logging
from queue import Queue  
import json
import random
from mona import mona

logging.basicConfig(level=logging.DEBUG, 
                    filename='output.log',
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

random_cost_flag = False
class WebVideoStream:
	
	def __init__(self, src="../videos/test_baofeng.mp4"):
		# 1080p D:\\kankan\\backup\\Automata.2014.1080p.BluRay.x264.YIFY.mp4
		# 720p  C:\\Tools\\titan_test.mp4
		self.config = Config()

		self.args = {}
		self.init_config()
		
		# initialize the file video stream along with the boolean
		# used to indicate if the thread should be stopped or not
		os.environ["OPENCV_VIDEOIO_DEBUG"] = "1"
		os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
		encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),15]
		self.stream = cv2.VideoCapture(src)
		
		self.stopped = False
		self.requesting = False
		self.request = False
		self.quit = False

		self.frame_id = 0
		self.delay_timer = int(time.time()*1000)

		#delay between reading a frame in update()
		self.push_sleep = 0.001  
		self.push_sleep_min = 0.001
		self.push_sleep_max = 0.2

		self.recv_fps = 0

		#控制信息相关
		self.server = mona(type='server').Server(self.args)

		# intialize thread and lock
		self.thread = Thread(target=self.update, args=())
		self.thread.daemon = True
		
	def init_config(self):
		config = self.config
		# 初始化连接信息
		self.client_ip = config.get("address", "client_ip")
		self.client_port = config.get("address", "client_port")
		self.server_ip = config.get("address", "server_ip")
		self.server_port = config.get("address", "server_port")
		self.ack_port = config.get("address", "ack_port")

		self.args['client_address'] = (self.client_ip, int(self.client_port))
		self.args['server_address'] = (self.server_ip, int(self.server_port))
		self.args['ack_address'] = (self.server_ip, int(self.ack_port))
		self.args['frame_pieces'] = int(config.get("server", "frame_pieces"))
		self.args['send_queue_size'] = int(config.get("server", "send_queue_size"))
		self.args['recv_queue_size'] = int(config.get("server", "recv_queue_size"))

		self.args['w'] =  int(config.get("camera", "w"))
		self.args['h'] = int(config.get("camera", "h"))
		self.args['d'] = int(config.get("camera", "d"))
		self.frame_size = self.args['w'] * self.args['h']
		self.frame_size_3d = self.args['w'] * self.args['h'] * self.args['d']
	
	def start(self):
		# start a thread to read frames from the file video stream
		self.thread.start()  # start the update thread 
		
		return self

	#不断读取帧并打包成数据包，放入发送队列
	def update(self):
		time_count = time.time()
		frame_fps_count = 0
		# keep looping infinitely until the thread is stopped
		while True:
			# 
			# time.sleep(self.push_sleep)
			if(frame_fps_count>=20):
				time_delta = time.time() - time_count
				time_count = time.time()
				# print(time_delta)
				if(time_delta>0):
					push_fps = 20.0 / time_delta
					print('push_fps: ', push_fps)
				frame_fps_count = 0
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return


			# otherwise, read the next frame from the stream
			(grabbed, frame_raw) = self.stream.read()
			# print('read frame cost:', time.time()-time_count)
			
			# if(not self.server.control_mess_buffer_is_empty()):
			# 	control_info = self.server.get_control_message()
			# 	# uniform random delay 10ms~50ms
			# 	if(random_cost_flag):
			# 		time_cost = random.uniform(0,1)/25 + 0.01
			# 		time.sleep(time_cost)

					
				# print('cost {} ms! and the size of the control_info_buffer is {}'.format(time_cost, self.server.control_info_buffer.qsize()))
			frame_raw = cv2.resize(frame_raw,(self.args['w'], self.args['h']), cv2.INTER_NEAREST)   #cost 10ms
			# print('resize cost:', time.time()-time_count)  
			# self.server.send_frame(frame_raw)   #cost 20ms
			cv2.imshow('img', frame_raw)
			if(cv2.waitKey(1) & 0xFF==ord('q')):
				break
			self.frame_id += 1
			frame_fps_count+=1
			# print('send frame cost:', time.time()-time_count)

		return

	def Q_stuck_control(self):
		if self.piece_fps == 0: return False # 为零表示还没有变化
		if self.piece_fps > self.packer.send_fps:
			self.push_sleep = min(self.push_sleep + 0.01, self.push_sleep_max)
			return True
		if self.piece_fps < self.packer.send_fps:
			self.push_sleep = max(self.push_sleep - 0.01, self.push_sleep_min)
		return False
	
	def send_stuck_control(self):
		if self.recv_fps == 0: return False
		if self.recv_fps > self.packer.recv_fps_limit:
			self.send_sleep = min(self.send_sleep + 0.01, self.send_sleep_max)
			return True
		if self.recv_fps < self.packer.recv_fps_limit:
			self.send_sleep = max(self.send_sleep - 0.01, self.send_sleep_min)
		return False


def SendVideo():

	wvs = WebVideoStream().start()   #启动update和recv_thread
	running = True
	# wvs.update()
	while running:
		if cv2.waitKey(1) & 0xFF == ord('q'):
			running = False
			continue




				
	exit(0)	

	
if __name__ == '__main__':
	SendVideo()
