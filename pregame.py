from direct.gui.DirectGui		import DirectEntry, DirectFrame, DirectButton
from direct.gui.DirectGui		import DGG
from direct.gui.OnscreenText	import OnscreenText
from pandac.PandaModules		import Vec3, TextNode

from game						import GameData
from user 						import User

class Pregame():
	def __init__(self, showbase):
		self.showbase = showbase
		
		self.ready = False

		self.background = DirectFrame(
			frameSize = (-1, 1, -1, 1),
			frameTexture  = 'media/gui/mainmenu/menu.png',
			parent = self.showbase.render2d,
		)

		self.title = OnscreenText(
			text   = 'Lobby!',
			fg     = (1, 1, 1, 1),
			parent = self.background,
			pos    = (-0.6, 0.1),
			scale  = 0.06
		)

		self.buttons = []
		controlButtons = Vec3(-0.60, 0, -0.79)
		# Toggle ready
		p = controlButtons + Vec3(-0.25, 0, 0)
		self.toggleReadyButton = DirectButton(
			text = 'Ready/Unready',
			pos = p,
			scale = 0.048,
			relief = DGG.GROOVE,
			command = self.toggleReady,
		)
		self.buttons.append(self.toggleReadyButton)
		# Disconnect
		p = controlButtons + Vec3(0.0, 0.0, 0.0)
		self.disconnectButton = DirectButton(
			text = 'Disconnect',
			pos = p,
			scale = 0.048,
			relief = DGG.GROOVE,
			command = self.disconnect,
		)
		self.buttons.append(self.disconnectButton)

		# Send message
		p = controlButtons + Vec3(0.25, 0.0, 0.0)
		self.sendMessageButton = DirectButton(
			text = 'Send Message',
			pos = p,
			scale = 0.048,
			relief = DGG.GROOVE,
			command = self.sendMessage,
			extraArgs = [''],
		)
		self.buttons.append(self.sendMessageButton)
		# Message input
		self.message = DirectEntry(
			command = self.sendMessage,
			focusInCommand = self.clearText,
			frameSize   = (-3, 3, -.5, 1),
			initialText = '',
			parent      = self.buttons[2],
			pos         = (0, -0.6, -1.5),
			text_align  = TextNode.ACenter,
		)

		self.showbase.gameData = GameData()

		self.showbase.users = []

		self.hide()

	def clearText(self):
		self.message.set('')

	def reset(self):
		self.messages = []
		self.showbase.users = []

	def updateLobby(self, task):
		temp = self.showbase.client.getData()
		for package in temp:
			if len(package) == 2:
				print 'Received: ', str(package)
				if package[0] == 'chat':
					if len(package[1]) == 2:
						self.messages.append(package[1])
						print self.messages
				elif package[0] == 'client':
					self.showbase.users.append(User(package[1]))
					for user in self.showbase.users:
						print user.name, user.ready
					print 'all users'
				elif package[0] == 'ready':
					for user in self.showbase.users:
						if user.name == package[1][0]:
							user.ready = package[1][1]
					for user in self.showbase.users:
						print user.name, user.ready
					print 'all users'
				elif package[0] == 'disconnect':
					for user in self.showbase.users:
						if user.name == package[1]:
							self.showbase.users.remove(user)
					for user in self.showbase.users:
						print user.name, user.ready
					print 'all users'
				elif package[0] == 'gamedata':
					self.showbase.gameData.unpackageData(package[1])
				elif package[0] == 'state':
					print 'state: ', package[1]
					if package[1] == 'preround':
						self.showbase.startRound()
						return task.done
		return task.again
	
	def toggleReady(self):
		self.ready = not self.ready
		self.showbase.client.sendData(('ready', self.ready))
		
	def disconnect(self):
		self.showbase.client.sendData(('disconnect', 'disconnect'))
		self.showbase.authCon = self.showbase.client
		self.showbase.returnToMenu()
	
	def sendMessage(self, message):
		if message == '':
			message = self.message.get()
		if message != '':
			self.showbase.client.sendData(('chat', message))
			self.message.set('')

	def hide(self):
		self.background.hide()
		self.message.hide()
		for b in self.buttons:
			b.hide()

		self.showbase.taskMgr.remove('Update Lobby')
	
	def show(self):
		self.background.show()
		self.message.show()
		for b in self.buttons:
			b.show()

		# Add the game loop procedure to the task manager.
		self.showbase.taskMgr.add(self.updateLobby, 'Update Lobby')
