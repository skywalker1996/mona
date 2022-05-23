

class rate_control_module(object):
	def __init__(self, frame_pieces):

		self.frame_pieces = frame_pieces
		# self.sending_delay_max = 1 / (60*frame_pieces)
		# self.server_sending_delay = self.sending_delay_max

		self.rec_window = 50

		self.cold_start = True

		self.network_delay_rec = [0,0]   #(min, max)
		self.packet_loss_rec = [0,0]
		self.send_delay_rec = [0,0]

		self.network_delay_g_rec = [0]*self.rec_window  # stroe previous gradients 
		self.send_delay_g_rec = [0]*self.rec_window  # stroe previous gradients  
		self.packet_loss_g_rec = [0]*self.rec_window


		self.network_delay_g2_rec = [0]*self.rec_window  # stroe previous gradients  
		self.packet_loss_g2_rec = [0]*self.rec_window

		self.utility_rec = [0]*self.rec_window

		state_list = ['step_1', 'step_2', 'action']
		self.state = 'step_1'

		self.sending_delay_max = 0.1
		self.sending_delay_min = 0.001
		self.server_sending_delay = self.sending_delay_max*0.8
		self.step_size = 0.001


		self.utility_part_rec = [0,0]

	def compute_utility(self, monitor_params):

		# monitor_params = {'network_delay':[], 'packet_loss', 'send_queue_delay', 'server_sending_delay'}
		network_delay = monitor_params['network_delay']
		packet_loss = monitor_params["packet_loss"]
		send_queue_delay = monitor_params["send_queue_delay"]
		# server_sending_delay = monitor_params["server_sending_delay"]


		network_delay_min = min(network_delay) 
		network_delay_max = max(network_delay)
		send_delay_min = min(send_queue_delay) 
		send_delay_max = max(send_queue_delay)
		packet_loss_min = min(packet_loss)
		packet_loss_max = max(packet_loss)

		if(self.cold_start):
			self.network_delay_rec = [network_delay_min, network_delay_max]
			self.send_delay_rec = [send_delay_min, send_delay_max]
			self.packet_loss_rec = [packet_loss_min, packet_loss_max]
			self.cold_start = False
			return 0.1, [0.1,0.1,0.1]

		## network delay 
		network_delay_min_g = network_delay_min - self.network_delay_rec[0]
		network_delay_max_g = network_delay_max - self.network_delay_rec[1]

		network_delay_g = 0.7*network_delay_min_g/self.network_delay_rec[0] + 0.3*network_delay_max_g/self.network_delay_rec[1]

		self.network_delay_g_rec = self.network_delay_g_rec[1:] + [network_delay_g]

		## send delay
		send_delay_min_g = send_delay_min - self.send_delay_rec[0]
		send_delay_max_g = send_delay_max - self.send_delay_rec[1]

		# send_delay_g = 0.7*send_delay_min_g/self.send_delay_rec[0] + 0.3*send_delay_max_g/self.send_delay_rec[1]

		# self.send_delay_g_rec = self.send_delay_g_rec[1:] + [send_delay_g]


		packet_loss_min_g = packet_loss_min - self.packet_loss_rec[0]
		packet_loss_max_g = packet_loss_max - self.packet_loss_rec[1]
		if(self.packet_loss_rec[0] > 0.001 and self.packet_loss_rec[1] > 0.001):
			packet_loss_g = 0.7*packet_loss_min_g/self.packet_loss_rec[0] + 0.3*packet_loss_max_g/self.packet_loss_rec[1]
		else:
			packet_loss_g = 0.7*packet_loss_min_g + 0.3*packet_loss_max_g

		self.packet_loss_g_rec = self.packet_loss_g_rec[1:] + [packet_loss_g]


		self.network_delay_rec = [network_delay_min, network_delay_max]
		self.packet_loss_rec = [packet_loss_min, packet_loss_max]
		self.send_delay_rec = [send_delay_min, send_delay_max]

		self.network_delay_g2_rec = self.network_delay_g2_rec[1:] + [self.network_delay_g_rec[-1] - self.network_delay_g_rec[-2]]
		self.packet_loss_g2_rec = self.packet_loss_g2_rec[1:] + [self.packet_loss_g_rec[-1] - self.packet_loss_g_rec[-2]]



		send_rate_part = (1 / self.server_sending_delay)/5
		network_part = -100 * network_delay_g - 100 * packet_loss_g
		send_queue_part = -send_queue_delay[-1] if send_queue_delay[-1] > 30 else 0 
		
		utility =  send_rate_part + network_part + send_queue_part
		utility_part = [send_rate_part, network_part, send_queue_part]

		self.utility_rec = self.utility_rec[1:] + [utility]
		# print('compute the utility = ', utility)
		return utility, utility_part

	def action(self, monitor_params):
		#decrease the sending delay
		if(self.state == 'step_1'):

			self.state = 'step_2'
			utility,utility_part = self.compute_utility(monitor_params)
			if(self.server_sending_delay<=self.sending_delay_min):
				return self.server_sending_delay, utility
			return self.server_sending_delay-self.step_size, utility

		#increase the sending delay
		elif(self.state == 'step_2'):
			self.state = 'action'
			utility,utility_part = self.compute_utility(monitor_params)
			self.utility_part_rec[0] = utility_part  #utility for decreasing sending delay

			if(self.server_sending_delay>=self.sending_delay_max):
				return self.server_sending_delay, utility
			return self.server_sending_delay+self.step_size, utility

		elif(self.state == 'action'):
			self.state = 'step_1'
			#take actions
			utility,utility_part = self.compute_utility(monitor_params)
			self.utility_part_rec[1] = utility_part #utility for increasing sending delay

			delta = self.utility_rec[-1] - self.utility_rec[-2]
			delta_part = [self.utility_part_rec[1][i]-self.utility_part_rec[0][i] for i in range(3)]
			# print()
			# print()
			# print('******** Get the delta value = {}'.format(delta))
			# print('******** Get the delta_part value = {}'.format(delta_part))
			if(delta > 0):

				if(self.server_sending_delay>=self.sending_delay_max):
					self.server_sending_delay -= 3*self.step_size
					# print('exceed max value, change server sending delay to {}!'.format(self.server_sending_delay))
				else:
					self.server_sending_delay += self.step_size
					# print('Increase server sending delay to {}!'.format(self.server_sending_delay))

			if(delta < 0):

				if(self.server_sending_delay<=self.sending_delay_min):
					self.server_sending_delay += 3*self.step_size
					print('exceed min value, change server sending delay to {}!'.format(self.server_sending_delay))
				else:
					self.server_sending_delay -= self.step_size
					print('Decrease server sending delay to {}!'.format(self.server_sending_delay))

			return self.server_sending_delay, utility

	def get_non_zero(self, List):
		return [List[i] for i in range(len(List)) if List[i]>0]


