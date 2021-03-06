from pandac.PandaModules import loadPrcFileData
loadPrcFileData("",
"""
	sync-video 1
	frame-rate-meter-update-interval 0.5
	show-frame-rate-meter 1
	window-type none
"""
)

from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionListener
from pandac.PandaModules import QueuedConnectionReader, ConnectionWriter
from pandac.PandaModules import NetDatagram
from pandac.PandaModules import PointerToConnection, NetAddress
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.task.Task import Task
from direct.showbase.ShowBase import ShowBase

import ConfigParser
from client							import Client
from game							import Game, GameData
from user 							import User

import rencode

gameTick = 1.0 / 30.0

class Server(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		# Server Networking handling stuff
		self.compress = False

		self.cManager = QueuedConnectionManager()
		self.cListener = QueuedConnectionListener(self.cManager, 0)
		self.cReader = QueuedConnectionReader(self.cManager, 0)
		self.cWriter = ConnectionWriter(self.cManager, 0)

		self.tempConnections = []
		self.unauthenticatedUsers = []
		self.users = []

		self.passedData = []

		self.connect(9099, 1000)
		self.startPolling()

		self.attemptAuthentication()
		
		self.taskMgr.doMethodLater(0.5, self.lobbyLoop, 'Lobby Loop')

	def connect(self, port, backlog = 1000):
		# Bind to our socket
		tcpSocket = self.cManager.openTCPServerRendezvous(port, backlog)
		self.cListener.addConnection(tcpSocket)

	def startPolling(self):
		self.taskMgr.add(self.tskListenerPolling, "serverListenTask", -40)
		self.taskMgr.add(self.tskDisconnectPolling, "serverDisconnectTask", -39)

	def tskListenerPolling(self, task):
		if self.cListener.newConnectionAvailable():
			rendezvous = PointerToConnection()
			netAddress = NetAddress()
			newConnection = PointerToConnection()

			if self.cListener.getNewConnection(rendezvous, netAddress, newConnection):
				newConnection = newConnection.p()
				newConnection.setNoDelay(True)
				self.tempConnections.append(newConnection)	# Remember connection
				self.cReader.addConnection(newConnection)	# Begin reading connection
		return Task.cont

	def tskDisconnectPolling(self, task):
		while self.cManager.resetConnectionAvailable() == True:
			connPointer = PointerToConnection()
			self.cManager.getResetConnection(connPointer)
			connection = connPointer.p()
			
			# Remove the connection we just found to be "reset" or "disconnected"
			self.cReader.removeConnection(connection)
			
			# remove from our activeConnections list
			if connection in self.tempConnections:
				self.tempConnections.remove(connection)
			for user in self.unauthenticatedUsers:
				if connection == user.connection:
					self.unauthenticatedUsers.remove(user)
			for user in self.users:
				if connection == user.connection:
					user.connection = None
					self.passData(('disconnect', user.name), None)
		
		return Task.cont

	def broadcastData(self, data):
		# Broadcast data out to all users
		for user in self.users:
			if user.connection:
				self.sendData(data, user.connection)

	def processData(self, netDatagram):
		myIterator = PyDatagramIterator(netDatagram)
		return self.decode(myIterator.getString())

	def getUsers(self):
		# return a list of all users
		return self.users

	def encode(self, data, compress = False):
		# encode(and possibly compress) the data with rencode
		return rencode.dumps(data, compress)

	def decode(self, data):
		# decode(and possibly decompress) the data with rencode
		return rencode.loads(data)

	def sendData(self, data, con):
		myPyDatagram = PyDatagram()
		myPyDatagram.addString(self.encode(data, self.compress))
		self.cWriter.send(myPyDatagram, con)

	def passData(self, data, connection):
		self.passedData.append((data, connection))

	def getData(self):
		data = []
		for passed in self.passedData:
			data.append(passed)
			self.passedData.remove(passed)
		while self.cReader.dataAvailable():
			datagram = NetDatagram()
			if self.cReader.getData(datagram):
				if datagram.getConnection() in self.tempConnections:
					self.processTempConnection(datagram)
					continue
				for authed in self.users:
					if datagram.getConnection() == authed.connection:
						data.append((self.processData(datagram), datagram.getConnection()))
		return data

	def processTempConnection(self, datagram):
		connection = datagram.getConnection()
		package = self.processData(datagram)
		if len(package) == 2:
			if package[0] == 'username':
				print 'attempting to authenticate', package[1]
				self.tempConnections.remove(connection)
				if not self.online:
					user = User(package[1], connection)
					# confirm authorization
					self.sendData(('auth', user.name), user.connection)
					self.updateClient(user)
					self.users.append(user)
				else:
					self.client.sendData(('auth', package[1]))
					self.unauthenticatedUsers.append(User(package[1], connection))

	def attemptAuthentication(self):
		config = ConfigParser.RawConfigParser()
		config.read('server.cfg')
		self.SERVER_NAME = config.get('SERVER DETAILS', 'serverName')

		config = ConfigParser.RawConfigParser()
		config.read('master.cfg')
		self.LOGIN_IP = config.get('MASTER SERVER CONNECTION', 'masterIp')
		self.LOGIN_PORT = config.getint('MASTER SERVER CONNECTION', 'masterPort')

		# Client for connecting to main server for showing exists and receiving clients
		self.client = Client(self, self.LOGIN_IP, self.LOGIN_PORT, compress = True)
		if self.client.getConnected():
			self.client.sendData(('server', self.SERVER_NAME))
			self.taskMgr.add(self.clientValidator, 'Client Validator')
			self.client.sendData(('state', 'lobby'))
			self.online = True
		else:
			# client not connected to login/auth server
			print 'Could not connect to Authentication Server.'
			print 'Server is not in online mode. No Authentication will happen for clients.'
			print 'Restart Server to attempt to connect to Authentication Server.'
			self.client = None
			self.online = False

	def clientValidator(self, task):
		temp = self.client.getData()
		for package in temp:
			if len(package) == 2:
				if package[0] == 'auth':
					print 'User authenticated: ', package[1]
					for user in self.unauthenticatedUsers:
						if user.name == package[1]:
							# confirm authorization
							self.sendData(('auth', user.name), user.connection)
							# send all required data to user
							self.updateClient(user)
							# all authenticated users
							self.users.append(user)
							self.unauthenticatedUsers.remove(user)
							print 'confirmation sent to ', package[1]
							break
				elif package[0] == 'fail':
					print 'User failed authentication: ', package[1]
					for user in self.unauthenticatedUsers:
						if user.name == package[1]:
							self.sendData(('fail', user.name), user.connection)
							self.unauthenticatedUsers.remove(user)
							break
		return task.again

	def updateClient(self, user):
		for existing in self.users:
			if existing.name != user.name:
				self.sendData(('client', existing.name), user.connection)
				self.sendData(('ready', (existing.name, existing.ready)), user.connection)
				if existing.connection:
					self.sendData(('client', user.name), existing.connection)
		self.sendData(('client', user.name), user.connection)

	def lobbyLoop(self, task):
		temp = self.getData()
		for package in temp:
			if len(package) == 2:
				print "Received: ", str(package)
				packet = package[0]
				connection = package[1]
				if len(packet) == 2:
					# check to make sure connection has username
					for user in self.users:
						if user.connection == connection:
							# if chat packet
							if packet[0] == 'chat':
								print 'Chat: ', packet[1]
								# Broadcast data to all clients ("username: message")
								self.broadcastData(('chat', (user.name, packet[1])))
							# else if ready packet
							elif packet[0] == 'ready':
								print user.name, ' changed readyness!'
								user.ready = packet[1]
								self.broadcastData(('ready', (user.name, user.ready)))
							# else if disconnect packet
							elif packet[0] == 'disconnect':
								print user.name, ' is disconnecting!'
								self.users.remove(user)
								self.broadcastData(('disconnect', user.name))
							# break out of for loop
							break
		# if all players are ready and there is X of them
		gameReady = True
		# if there is any clients connected
		if self.getUsers() == []:
			gameReady = False
		for user in self.users:
			if not user.ready:
				gameReady = False
		if gameReady:
			self.prepareGame()
			return task.done
		return task.again
		
	def prepareGame(self):
		if self.camera:
			# Disable Mouse Control for camera
			self.disableMouse()
			
			self.camera.setPos(0, 0, 500)
			self.camera.lookAt(0, 0, 0)

		self.gameData = GameData(True)
		
		# game data
		self.broadcastData(('gamedata', self.gameData.packageData()))
		self.broadcastData(('state', 'preround'))
		if self.online:
			self.client.sendData(('state', 'preround'))
		print "Preparing Game"
		self.gameTime = 0
		self.tick = 0

		usersData = []
		for user in self.users:
			usersData.append(user.gameData)
		self.game = Game(self, usersData, self.gameData)
		self.taskMgr.doMethodLater(0.5, self.roundReadyLoop, 'Game Loop')
		print "Round ready State"
		
	def roundReadyLoop(self, task):
		temp = self.getData()
		for package in temp:
			if len(package) == 2:
				print "Received: ", str(package)
				if len(package[0]) == 2:
					for user in self.users:
						if user.connection == package[1]:
							if package[0][0] == 'round':
								if package[0][1] == 'sync':
									user.sync = True
		# if all players are ready and there is X of them
		roundReady = True
		# if there is any clients connected
		for user in self.users:
			if user.sync == False:
				roundReady = False
		if roundReady:
			self.taskMgr.doMethodLater(2.5, self.gameLoop, 'Game Loop')
			print "Game State"
			return task.done
		return task.again
	
	def gameLoop(self, task):
		# process incoming packages
		temp = self.getData()
		for package in temp:
			if len(package) == 2:
				# check to make sure connection has username
				for user in self.users:
					if user.connection == package[1]:
						user.gameData.processUpdatePacket(package[0])
		# get frame delta time
		dt = self.taskMgr.globalClock.getDt()
		self.gameTime += dt
		# if time is less than 3 secs (countdown for determining pings of clients?)
		# tick out for clients
		while self.gameTime > gameTick:
			# update all clients with new info before saying tick
			for user in self.users:
				updates = user.gameData.makeUpdatePackets()
				for packet in updates:
					self.broadcastData((user.name, packet))
			self.broadcastData(('tick', self.tick))
			self.gameTime -= gameTick
			self.tick += 1
			# run simulation
			if not self.game.runTick(gameTick):
				print 'Game Over'
				# send to all players that game is over (they know already but whatever)
				# and send final game data/scores/etc
				for user in self.users:
					user.ready = False
				self.taskMgr.doMethodLater(0.5, self.lobbyLoop, 'Lobby Loop')
				return task.done
		return task.cont

server = Server()
server.run()
