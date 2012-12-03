class UserData():
	def __init__(self):
		self.new_dest = False
		self.centipede = None
		self.thisPlayer = False

	def makeUpdatePackets(self):
		packets = []
		# new destination
		if self.new_dest:
			packets.append(('update_dest', self.centipede.get_destination_update()))
			self.new_dest = False
		return packets

	def processUpdatePacket(self, packet):
		if len(packet) == 2:
			if packet[0] == 'update_dest':
				self.centipede.set_destination(packet[1])
				self.new_dest = True

class User():
	def __init__(self, name, connection = None):
		self.name = name
		self.connection = connection
		self.ready = False
		self.sync = False
		self.gameData = UserData()
