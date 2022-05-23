import time
from lib.monitorFlux import MonitorFlux
import cv2
from configs.config import Config

config = Config('global.conf')

db_para = {}
db_para['url'] = config.get('database', 'url')
db_para['token'] = config.get('database', 'token')
db_para['org'] = config.get('database', 'org')
db_para['bucket'] = config.get('database', 'bucket')

# tags = {'version':'0.4'}

targets = []
targets.append({'measurement': 'Experiments', 'field_name': 'network_delay', 'tags': None, 'time_range': '30s' })
targets.append({'measurement': 'Experiments', 'field_name': 'packet_loss', 'tags': None, 'time_range': '30s' })
targets.append({'measurement': 'Experiments', 'field_name': 'sending_queue_delay', 'tags': None, 'time_range': '30s'})
targets.append({'measurement': 'Experiments', 'field_name': 'utility', 'tags': None, 'time_range': '30s'})
targets.append({'measurement': 'Experiments', 'field_name': 'recv_buffer_size', 'tags': None, 'time_range': '30s'})
targets.append({'measurement': 'Experiments', 'field_name': 'server_sending_delay', 'tags': None, 'time_range': '30s'})


Monitor = MonitorFlux(db_para=db_para, plot_number=5, fig_size=(15,15),monitor_targets=targets)

# results = Monitor.pullData(measurement='state_monitor',tags=None, time_range='5d')
# print(results)

running = True
while running:
	if cv2.waitKey(1) & 0xFF == ord('q'):
		running = False
		continue
	Monitor.updateMonitor()
	time.sleep(0.2)

