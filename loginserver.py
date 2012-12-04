from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionListener
from pandac.PandaModules import QueuedConnectionReader, ConnectionWriter
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from pandac.PandaModules import NetDatagram
from direct.task.Task import Task
from pandac.PandaModules import *
from direct.showbase.ShowBase import ShowBase
from db import ClientDataBase
import rencode

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("",
"""
	window-type none
"""
)

class Client:
	def __init__(self, name, connection):
		self.name = name
		self.connection = connection
		print 'Client connected: ', name, 'From: ', connection.getAddress()

class Server:
	def __init__(self, name, connection):
		self.name = name
		self.connection = connection
		self.state = 'starting'
		print 'Server connected: ', name, 'From: ', connection.getAddress()

class Chat:
	def __init__(self, name, connection):
		self.name = name
		self.private = False
		self.connection = connection
		print 'Chat Server connected: ', name, 'From: ', connection.getAddress()

# Login server Core.
class LoginServer(ShowBase):
	def __init__(self, port, backlog = 1000, compress = False):
		ShowBase.__init__(self)

		self.compress = compress

		self.cManager = QueuedConnectionManager()
		self.cListener = QueuedConnectionListener(self.cManager, 0)
		self.cReader = QueuedConnectionReader(self.cManager, 0)
		self.cWriter = ConnectionWriter(self.cManager,0)
		
		self.clientdb = ClientDataBase()
		if not self.clientdb.connected:
			self.clientdb = None
			print 'Login Server failed to start...'
		else:
			# This is for pre-login
			self.tempConnections = []
			
			# This is for authed clients
			self.activeClients = []
			# This is for authed servers
			self.activeServers = []
			# This is for authed chat servers
			self.activeChats = []
			
			self.connect(port, backlog)
			self.startPolling()
			
			taskMgr.doMethodLater(0.5, self.lobbyLoop, 'Lobby Loop')
			
			print 'Login Server operating...'

	def connect(self, port, backlog = 1000):
		# Bind to our socket
		tcpSocket = self.cManager.openTCPServerRendezvous(port, backlog)
		self.cListener.addConnection(tcpSocket)

	def startPolling(self):
		taskMgr.add(self.tskListenerPolling, "serverListenTask", -40)
		taskMgr.add(self.tskDisconnectPolling, "serverDisconnectTask", -39)

	def tskListenerPolling(self, task):
		if self.cListener.newConnectionAvailable():
			rendezvous = PointerToConnection()
			netAddress = NetAddress()
			newConnection = PointerToConnection()
			if self.cListener.getNewConnection(rendezvous, netAddress, newConnection):
				newConnection = newConnection.p()
				self.tempConnections.append(newConnection)
				self.cReader.addConnection(newConnection)
		return Task.cont

	def tskDisconnectPolling(self, task):
		while self.cManager.resetConnectionAvailable() == True:
			connPointer = PointerToConnection()
			self.cManager.getResetConnection(connPointer)
			connection = connPointer.p()
			
			# Remove the connection
			self.cReader.removeConnection(connection)
			# Check for if it was a client
			for client in self.activeClients:
				if client.connection == connection:
					self.activeClients.remove(client)
					break
			# then check servers
			for server in self.activeServers:
				if server.connection == connection:
					self.activeServers.remove(server)
					break
			# then check servers
			for chat in self.activeChats:
				if chat.connection == connection:
					self.activeChats.remove(chat)
					break
					
		return Task.cont

	def processData(self, netDatagram):
		myIterator = PyDatagramIterator(netDatagram)
		return self.decode(myIterator.getString())

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
		
	# This will check and do the logins.
	def auth(self, datagram): 
		# If in login state.
		con = datagram.getConnection()
		package = self.processData(datagram)
		if len(package) == 2:
			if package[0] == 'create':
				success, result = self.clientdb.addClient(package[1][0], package[1][1])
				if success:
					self.sendData(('createSuccess', result), con)
				else:
					self.sendData(('createFailed', result), con)
				return False
			if package[0] == 'client':
				userFound = False
				for client in self.activeClients:
					if client.name == package[1][0]:
						userFound = True
						self.sendData(('loginFailed', 'logged'), con)
						break
				if not userFound:
					valid, result = self.clientdb.validateClient(package[1][0], package[1][1])
					if valid:
						self.activeClients.append(Client(package[1][0], con))
						self.sendData(('loginValid', result), con)
						return True
					else:
						self.sendData(('loginFailed', result), con)
						return False
			# if server add it to the list of current active servers
			if package[0] == 'server':
				self.activeServers.append(Server(package[1], con))
				return True
			# if server add it to the list of current active servers
			if package[0] == 'chat':
				self.activeChats.append(Chat(package[1], con))
				return True

	def getData(self):
		data = []
		while self.cReader.dataAvailable():
			datagram = NetDatagram()
			if self.cReader.getData(datagram):
				if datagram.getConnection() in self.tempConnections:
					if self.auth(datagram):
						self.tempConnections.remove(datagram.getConnection())
					continue
				# Check if the data recieved is from a valid client.
				for client in self.activeClients:
					if datagram.getConnection() == client.connection:
						data.append(('client', self.processData(datagram), client))
						break
				# Check if the data recieved is from a valid server.
				for server in self.activeServers:
					if datagram.getConnection() == server.connection:
						data.append(('server', self.processData(datagram), server))
						break
				# Check if the data recieved is from a valid chat.
				for chat in self.activeChats:
					if datagram.getConnection() == chat.connection:
						data.append(('chat', self.processData(datagram), chat))
						break
		return data

	# handles new joining clients and updates all clients of chats and readystatus of players
	def lobbyLoop(self, task):
		# if in lobby state
		temp = self.getData()
		if temp != []:
			for package in temp:
				# handle client incoming packages here
				if package[0] == 'client':
					# This is where packages will come after clients connect to the server
					# will be things like requesting available servers and chat servers
					if package[1] == 'server_query':
						for server in self.activeServers:
							if server.state == 'lobby':
								self.sendData(
									('server', (server.name, str(server.connection.getAddress()))),
									package[2].connection)
						self.sendData(
							('final', 'No more servers'),
							package[2].connection)
				# handle server incoming packages here
				elif package[0] == 'server':
					# auth
					# game state change
					if len(package[1]) == 2:
						if package[1][0] == 'auth':
							clientAuth = False
							print 'Attempting Authentication on: ', package[1][1]
							for client in self.activeClients:
								if client.name == package[1][1]:
									clientAuth = True
									break
							if clientAuth:
								self.sendData(('auth', client.name), package[2].connection)
							else:
								self.sendData(('fail', package[1][1]), package[2].connection)
						elif package[1][0] == 'state':
							package[2].state = package[1][1]
				# handle chat server incoming packages here
				elif package[0] == 'chat':
					print 'Authorized chat server sent package'
					# handle packages from the chat servers
					# like making public/private
					# authing clients
		return task.again

print 'STARTING LOGIN SERVER'
loginServer = LoginServer(9098, compress = True)
loginServer.run()
