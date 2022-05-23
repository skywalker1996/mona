from threading import Thread, Lock
from queue import Queue, PriorityQueue
import socket
import time
import cv2
import numpy
import sys
from configs.config import Config
import logging
import json
from lib.mona import mona


# logging.basicConfig(level=logging.DEBUG, 
#                     filename='logs/output-client.log',
# 					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


class FramePack(object):
	def __init__(self, ctime, frame):
		self.ctime = ctime
		self.frame = frame


class VideoStreamClient:
	def __init__(self, queue_size=128):
		self.stopped = False
		self.args = {}
		self.config = Config('cfg_app.conf')

		self.init_config()

		#控制信息的id
		self.control_id = 0
		self.last_frame_time = int(time.time()*1000)
		self.require = True

		#用户操作时延
		self.control_delay = 0
		self.delay_timer = int(time.time()*1000)
		self.receive_fps = 0

		self.client = mona(type='client').Client(self.args)

		print('NetVideoStream init successfully!')

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
		self.args['encode_param'] = int(config.get("server", "encode_quality"))

		self.args['w'] =  int(config.get("camera", "w"))
		self.args['h'] = int(config.get("camera", "h"))
		self.args['d'] = int(config.get("camera", "d"))
		self.frame_size = self.args['w'] * self.args['h']
		self.frame_size_3d = self.args['w'] * self.args['h'] * self.args['d']
	
	
	def start(self):

		control_thread = Thread(target=self.control_thread, args=())
		control_thread.daemon = True
		control_thread.start()

		return self


	def control_thread(self):
		print('start the control thread!')
		while(True):
			control_info = {}
			control_info['type'] = 'control'
			control_info['id'] = self.control_id
			control_info['pressed_key'] = ['Q','CTRL']
			control_info['released_key'] = ['S']
			control_info['mouse_location'] = [128,72]
			control_info = json.dumps(control_info)
			self.control_id += 1
			time.sleep(0.05)
			self.client.send_control_message(control_info)



	def read_show(self):
		nvs = self.start()
		last_frame_time = time.time()
		tshow, fshow = 0, 0
		frame_counter = 0
		while True:
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
				
			now = time.time()
			frame = self.client.get_recv_img()

			if frame is not None:
				# frame = framePack.frame
				# frame_time = framePack.ctime

				# 更新和显示fps			
				if(frame_counter%20==0):
					if(frame_counter!=0):
						time_delta = time.time() - time_counter 
						nvs.receive_fps = int(20.0/time_delta) if time_delta!=0 else 0
					time_counter = time.time()
					frame_counter = 0


				cnow = int(time.time()*1000)
				if cnow - nvs.delay_timer > 200:
					nvs.delay_timer = cnow
					# control_delay = nvs.control_delay
					fshow = nvs.receive_fps
				
				# 记录上一帧时间
				last_frame_time = time.time()
				
				font                   = cv2.FONT_HERSHEY_SIMPLEX
				bottomLeftCornerOfText = (10,50)
				fontScale              = 1
				fontColor              = (0,0,255)
				lineType               = 2
				cv2.putText(frame, 'control Delay: ' + str(self.control_delay).ljust(3) + " ms, FPS:" + str(fshow).ljust(3),
					bottomLeftCornerOfText, 
					font, 
					fontScale,
					fontColor,
					lineType)
				cv2.imshow("Receive server", frame)
				frame_counter+=1

				

def ReceiveVideo():

	print('start read_show()')
	VideoStreamClient().read_show() # 一次性使用

	print("The server is quitting. ")
	cv2.destroyAllWindows()
 
if __name__ == '__main__':
	ReceiveVideo()