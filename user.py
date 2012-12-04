class UserData():
	def __init__(self):
		self.newDest = False
		self.centipede = None
		self.thisPlayer = False

	def makeUpdatePackets(self):
		packets = []
		# new destination
		if self.newDest:
			packets.append(('updateDest', self.centipede.getDestinationUpdate()))
			self.newDest = False
		return packets

	def processUpdatePacket(self, packet):
		if len(packet) == 2:
			if packet[0] == 'updateDest':
				self.centipede.setDestination(packet[1])
				self.newDest = True

class User():
	def __init__(self, name, connection = None):
		self.name = name
		self.connection = connection
		self.ready = False
		self.sync = False
		self.gameData = UserData()
