import sys 
import os.path as osp
sys.path.append(osp.abspath(osp.dirname(osp.dirname(__file__))))
from lib.rate_control import rate_control_module
from lib.influx_operator import InfluxOP
from lib.monitorFlux import MonitorFlux
import numpy as np


database='Experiments'
measurement = 'state_monitor'

Attribute_list = ['network_delay', 'packet_loss', 'sending_queue_delay', 'server_sending_delay', 'utility']

Attribute_buffer = {}


def Attr_statistic(results):

	for attr in Attribute_list:
		Attribute_buffer[attr] = []

	for data in results:
		for attr in Attribute_list:
			if(data[attr] is not None):
				if(attr is not 'utility' and data[attr]>=0):
					if(attr=='network_delay' and data[attr] >300):
						continue
					Attribute_buffer[attr].append(data[attr])
				elif(attr=='utility' and data[attr] is not None and data[attr]<10000):
					Attribute_buffer[attr].append(data[attr])
	# print(Attribute_buffer['server_sending_delay'])

	statistics = {}
	for attr in Attribute_list:
		print('processing {}'.format(attr))
		statistics[attr] = {}
		statistics[attr]['avg'] = np.mean(Attribute_buffer[attr])
		statistics[attr]['max'] = np.max(Attribute_buffer[attr])
		statistics[attr]['min'] = np.min(Attribute_buffer[attr])

	return statistics,Attribute_buffer


if __name__ == '__main__':

	db_addr = {'ip':'192.168.2.171', 'port': 8086}
	# db_addr = {'ip':'10.0.0.1', 'port': 8086}
	db_auth = {'username': 'zhijian', 'password': "huizhijian"}

	operator = MonitorFlux(db_addr=db_addr, db_auth=db_auth, db_name='Experiments')

	# demo = [{'network_delay': 11, 'packet_loss': 0.02, 'sending_queue_delay': 340}]
	# tags = {'version':'0.4'}



	# operator.pushData(database='rate_control',measurement = 'state_monitor', datapoints = demo, tags = tags )

	# results = operator.pullData(database='rate_control',measurement='state_monitor',tags=None, time_range='1d')


	# create database
	# results = operator.createDatabase(name='rate_control')


	# delete Date
	results = operator.deleteData(measurement = 'state_monitor', tags=None, time_before='5s')
	print(results)

	# pull data
	results = operator.pullData(measurement='state_monitor',tags=None, time_range='12m')
	if(results):
		print(len(results))
		statistics,Attribute_buffer = Attr_statistic(results)
		print()
		print(statistics)
# 
	# print(results[0])

	# x = [data['time'] for data in results[0]]
	# y = [data['network_delay'] for data in results[0]]
	# print(x)
	# print(y)

	# drop measurement
	# results = operator.dropMeasurement(database='Experiments',measurement='state_monitor')
	# print(results)

	# drop database
	# results = operator.dropDatabase(database='Experiments')