from queue import Queue, PriorityQueue

# class Pack(object):
# 	def __init__(self, idx, ctime):
# 		self.idx = idx
# 		self.ctime = ctime

# 	def __lt__(self, other):
# 		return self.ctime > other.ctime 

# Q = PriorityQueue(128)
# Q.put(Pack(2, 1548397750814))
# Q.put(Pack(1, 1548397750871))

# print(Q.get().ctime)
# print(Q.get().ctime)

# arr = []
# for i in range(10):
# 	arr.append(None)
# print(arr[3])


import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import numpy as np
import random
 
POINTS = 100

 
# fig, ax = plt.subplots()
# ax.set_ylim([0, 50])
# ax.set_xlim([0, POINTS])
# ax.set_autoscale_on(False)
# ax.grid(True)
# delay_record = [np.random.random() for i in range(100)]
# line_delay, = ax.plot(range(0,100), delay_record, label='Delay', color='cornflowerblue')
# ax.legend(loc='upper center', ncol=4, prop=font_manager.FontProperties(size=10))
 
 
# def sin_output(ax):

# 	global delay_record
# 	delay_record = delay_record[1:] + [random.random()]
# 	line_delay.set_ydata(delay_record)
# 	ax.draw_artist(lin)
# 	ax.figure.canvas.draw()

 
# timer = fig.canvas.new_timer(interval=100)
# timer.add_callback(sin_output, ax)
# timer.start()
# plt.show()

fig = plt.figure()

#Delay
delay_ax = plt.subplot(221)
delay_ax.set_ylim(0, 1)

delay_ax.set_autoscale_on(False)
delay_ax.grid(True)
delay_record = [np.random.random() for i in range(100)]
line_delay, = delay_ax.plot(range(0,100), delay_record, label='Delay', color='cornflowerblue')
delay_ax.legend(loc='upper center', ncol=4, prop=font_manager.FontProperties(size=10))
frame_id = 0
def plot_update(ax):
	
	global delay_record, packet_loss_record, frame_id
	delay_record = delay_record[1:] + [random.random()]
	line_delay.set_ydata(delay_record)
	line_delay.set_xdata(range(frame_id,frame_id+100))
	delay_ax.set_xlim(frame_id,frame_id+100)
	plt.draw()
	frame_id+=1

 
timer = fig.canvas.new_timer(interval=200)
timer.add_callback(plot_update, delay_ax)
timer.start()
plt.show()
