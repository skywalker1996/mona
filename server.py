from threading import Thread, Lock
import socket
import cv2
import numpy
import time
import sys
import os
from configs.config import Config
import logging
from queue import Queue  
import json
import random
from lib.mona import mona

# logging.basicConfig(level=logging.DEBUG, 
#                     filename='logs/output-server.log',
# 					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

random_cost_flag = False
class VideoStreamServer:
	
	def __init__(self, src="../videos/test_baofeng.mp4"):
		# 1080p D:\\kankan\\backup\\Automata.2014.1080p.BluRay.x264.YIFY.mp4
		# 720p  C:\\Tools\\titan_test.mp4
		self.config = Config('cfg_app.conf')

		self.args = {}
		self.init_config()
		
		# initialize the file video stream along with the boolean
		# used to indicate if the thread should be stopped or not
		os.environ["OPENCV_VIDEOIO_DEBUG"] = "1"
		os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
		
		self.stream = cv2.VideoCapture(src)
		
		self.stopped = False
		self.requesting = False
		self.request = False
		self.quit = False

		self.frame_id = 0
		self.delay_timer = int(time.time()*1000)

		#delay between reading a frame in update()
		self.push_sleep = float(self.config.get("server", "push_sleep"))
		self.push_sleep_min = float(self.config.get("server", "push_sleep_min"))
		self.push_sleep_max = float(self.config.get("server", "push_sleep_max"))

		self.recv_fps = 0

		#控制信息相关
		self.server = mona(type='server').Server(self.args)

		# intialize thread and lock
		self.thread = Thread(target=self.update, args=())
		self.thread.daemon = True

		print('Start the Server!')
		
	def init_config(self):
		config = self.config
		# 初始化连接信息
		self.client_ip = config.get("address", "client_ip")
		self.client_port = config.get("address", "client_port")
		self.server_ip = config.get("address", "server_ip")
		self.server_port = config.get("address", "server_port")
		self.ack_port = config.get("address", "ack_port")
		
		self.args['encode_param'] = int(config.get("server", "encode_quality"))
		self.args['client_address'] = (self.client_ip, int(self.client_port))
		self.args['server_address'] = (self.server_ip, int(self.server_port))
		self.args['ack_address'] = (self.server_ip, int(self.ack_port))

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

		print('Start sending frames!')
		time_count = time.time()
		frame_fps_count = 0
		# keep looping infinitely until the thread is stopped
		while True:
			# 
			time.sleep(self.push_sleep)
			if(frame_fps_count>=20):
				time_delta = time.time() - time_count
				time_count = time.time()
				# print(time_delta)
				if(time_delta>0):
					push_fps = 20.0 / time_delta
					# print('push_fps: ', push_fps)
				frame_fps_count = 0
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return


			# otherwise, read the next frame from the stream
			(grabbed, frame_raw) = self.stream.read()
			# print('read frame cost:', time.time()-time_count)
			
			if(not self.server.control_msg_buffer_is_empty()):
				control_info = self.server.get_control_message()
				# uniform random delay 10ms~50ms
				if(random_cost_flag):
					time_cost = random.uniform(0,1)/25 + 0.01
					time.sleep(time_cost)

					
				# print('cost {} ms! and the size of the control_info_buffer is {}'.format(time_cost, self.server.control_info_buffer.qsize()))
			frame_raw = cv2.resize(frame_raw,(self.args['w'], self.args['h']), cv2.INTER_NEAREST)   #cost 10ms
			# print('resize cost:', time.time()-time_count)  
			self.server.send_frame(frame_raw)   #cost 20ms
			self.frame_id += 1
			frame_fps_count += 1
			# print('send frame cost:', time.time()-time_count)

		return

def SendVideo():

	wvs = VideoStreamServer().start()   #启动update和recv_thread
	running = True
	while running:
		if cv2.waitKey(1) & 0xFF == ord('q'):
			running = False
			continue

		now1 = 1000 * time.time()
		network_delay, packet_loss = wvs.server.get_sending_status()

		send_fps = str(wvs.server.sending_fps).ljust(4)
		recv_fps = str(wvs.recv_fps).ljust(4)
		net_delay = str(network_delay).ljust(4)
		packet_loss = str(packet_loss*100).ljust(4)
		frame_id = str(wvs.frame_id).ljust(10)

		if now1 - wvs.delay_timer > 300:
		# if True:
			wvs.delay_timer = now1

			img = numpy.zeros((100, 1000,3), numpy.uint8)
			font                   = cv2.FONT_HERSHEY_SIMPLEX
			bottomLeftCornerOfText = (10,50)
			fontScale              = 0.7
			fontColor              = (255,255,255)
			lineType               = 2
			cv2.putText(img, 'Send FPS:' + send_fps + ", Packet Loss: " + packet_loss + "% , Net delay: " + net_delay+ "ms , Frame ID:" + frame_id,
				bottomLeftCornerOfText, 
				font, 
				fontScale,
				fontColor,
				lineType)
			cv2.imshow("Send clinet", img)
			# wvs.server.plot_update()
				
	exit(0)	

	
if __name__ == '__main__':
	SendVideo()
