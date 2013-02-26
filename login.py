from direct.gui.OnscreenText	import OnscreenText
from direct.gui.DirectGui		import DirectFrame, DirectButton, DirectEntry, DirectCheckButton
from direct.gui.DirectGui		import DGG
from pandac.PandaModules		import Vec3, TextNode

from client						import Client

import ConfigParser

class Login():
	def __init__(self, showbase):
		self.showbase = showbase
		
		self.background = DirectFrame(
			frameSize = (-1, 1, -1, 1),
			frameTexture  = 'media/gui/login/bg.png',
			parent = self.showbase.render2d,
		)

		### CONFIG LOADER ###
		config = ConfigParser.RawConfigParser()
		config.read('master.cfg')
		self.LOGIN_IP = config.get('MASTER SERVER CONNECTION', 'masterIp')
		self.LOGIN_PORT = config.getint('MASTER SERVER CONNECTION', 'masterPort')

		config = ConfigParser.RawConfigParser()
		config.read('client.cfg')
		self.storeUsername = config.getint('USERDATA', 'storeUsername')
		if self.storeUsername == 1:
			self.username = config.get('USERDATA', 'username')
		else:
			self.username = ''
		self.storePassword = config.getint('USERDATA', 'storePassword')
		if self.storePassword == 1:
			self.password = config.get('USERDATA', 'password')
		else:
			self.password = ''
		### CONFIG END ###

		self.loginScreen("Press 'Enter' to login")
		# draws the login screen

		self.usernameBox['focus'] = 1
		# sets the cursor to the username field by default

		self.showbase.accept('tab', self.cycleLoginBox)
		self.showbase.accept('shift-tab', self.cycleLoginBox)
		# enables the user to cycle through the text fields with the tab key
		# this is a standard feature on most login forms

		self.showbase.accept('enter', self.attemptLogin)         
		# submits the login form, or you can just click the Login button
		
		# checking variable to stop multiple presses of the button spawn multiple tasks
		self.requestAttempt = False
		
		self.showbase.authCon = Client(self.showbase, self.LOGIN_IP, self.LOGIN_PORT, compress = True)
		if not self.showbase.authCon.getConnected():
			self.updateStatus("Could not connect to the Login server\nOFFLINE MODE")
			self.showbase.online = False

	def updateConfig(self):
		config = ConfigParser.RawConfigParser()
		config.read('client.cfg')
		config.set('USERDATA', 'storeUsername', self.usernameStoreBox["indicatorValue"])
		config.set('USERDATA', 'storePassword', self.passwordStoreBox["indicatorValue"])
		if self.usernameStoreBox["indicatorValue"] == 1:
			config.set('USERDATA', 'username', self.usernameBox.get())
		if self.passwordStoreBox["indicatorValue"] == 1:
			config.set('USERDATA', 'password', self.passwordBox.get())
		with open('client.cfg', 'wb') as configfile:
			config.write(configfile)
	
	def loginScreen(self, statusText):
		# creates a basic login screen that asks for a username/password
		
		boxloc = Vec3(0.0, 0.0, 0.0)
		# all items in the login form will have a position relative to this
		# this makes it easier to shift the entire form around once we have
		# some graphics to display with it without having to change the
		# positioning of every form element

		# p is the position of the form element relative to the boxloc
		# coordinates set above it is changed for every form element
		p = boxloc + Vec3(-0.22, 0.09, 0.0)                                 
		self.usernameText = OnscreenText(text = "Username:", pos = p, scale = 0.05, bg = (0, 0, 0, 1), fg = (1, 1, 1, 1), align = TextNode.ARight)
		# "Username: " text that appears beside the username box

		p = boxloc + Vec3(-0.2, 0.0, 0.09)
		self.usernameBox = DirectEntry(text = "", pos = p, scale=.04, initialText = self.username, numLines = 1)
		# Username textbox where you type in your username
		
		p = boxloc + Vec3(0.4, 0.0, 0.09)
		self.usernameStoreBox = DirectCheckButton(text = "Save Username?", pos = p, scale = .04, indicatorValue = self.storeUsername)
		# Toggle to save/not save your username
		
		p = boxloc + Vec3(-0.22, 0.0, 0.0)       
		self.passwordText = OnscreenText(text = "Password:", pos = p, scale = 0.05, bg = (0,0,0,1), fg = (1, 1, 1, 1), align = TextNode.ARight)
		# "Password: " text that appears beside the password box

		p = boxloc + Vec3(-0.2, 0.0, 0.0)
		self.passwordBox = DirectEntry(text = "", pos = p, scale = .04, initialText = self.password, numLines = 1, obscured = 1)
		# Password textbox where you type in your password
		# Note - obscured = 1 denotes that all text entered will be replaced
		# with a * like a standard password box
		
		p = boxloc + Vec3(0.4, 0.0, 0.0)
		self.passwordStoreBox = DirectCheckButton(text = "Save Password?", pos = p, scale = .04, indicatorValue = self.storePassword)
		# Toggle to save/not save your username
		
		p = boxloc + Vec3(0, 0, -0.090)
		self.loginButton = DirectButton(text = "Login", pos = p, scale = 0.048, relief = DGG.GROOVE, command = self.attemptLogin)
		# The 'Quit' button that will trigger the Quit function
		# when clicked
		
		p = boxloc + Vec3(0.95, 0, -0.9)
		self.createAccButton = DirectButton(text = "Create Account", scale = 0.050, pos = p, relief = DGG.GROOVE, command = self.attemptCreateAccount)
		# Made a quick button for adding accounts. Its fugly

		p = boxloc + Vec3(1.20, 0, -0.9)
		self.quitButton = DirectButton(text = "Quit", pos = p, scale = 0.048, relief = DGG.GROOVE, command = self.showbase.quit)
		# The 'Quit' button that will trigger the Quit function
		# when clicked
		
		p = boxloc + Vec3(0, -0.4, 0)
		self.statusText = OnscreenText(text = statusText, pos = p, scale = 0.043, fg = (1, 0.5, 0, 1), align = TextNode.ACenter)
		# A simple text object that you can display an error/status messages
		# to the user

	def updateStatus(self, statusText):
		self.statusText.setText(statusText)
		# all this does is change the status text.

	def checkBoxes(self):
		# checks to make sure the user inputed a username and password:
		#       if they didn't it will spit out an error message
		self.updateStatus("")
		if self.usernameBox.get() == "":
			if self.passwordBox.get() == "":
				self.updateStatus("You must enter a username and password before logging in.")
			else:
				self.updateStatus("You must specify a username")
				self.passwordBox['focus'] = 0
				self.usernameBox['focus'] = 1
			return False
		elif self.passwordBox.get() == "":
			self.updateStatus("You must enter a password")
			self.usernameBox['focus'] = 0
			self.passwordBox['focus'] = 1
			return False
		# if both boxes are filled then return True
		return True

	def attemptLogin(self):
		if self.checkBoxes():
			self.showbase.username = self.usernameBox.get()
			self.updateStatus("Attempting to login...")
			self.request(self.usernameBox.get(), self.passwordBox.get(), 'client')
			
	def attemptCreateAccount(self):
		if self.checkBoxes():
			self.updateStatus("Attempting to create account and login...")
			self.request(self.usernameBox.get(), self.passwordBox.get(), 'create')
	
	def request(self, username, password, request):
		if not self.requestAttempt:
			# attempt to connect again if it failed on startup
			if self.showbase.authCon.getConnected():
				self.requestAttempt = True
				self.loginButton["state"] = DGG.DISABLED
				self.createAccButton["state"] = DGG.DISABLED
				self.showbase.authCon.sendData((request, (username, password)))
				self.showbase.username = username
				self.showbase.online = True
				self.showbase.taskMgr.doMethodLater(0.2, self.responseReader, 'Update Login')
			else:
				# client not connected to login/auth server so display message
				self.updateStatus("Offline Mode")
				self.showbase.username = username
				self.showbase.online = False
				self.updateConfig()
				self.showbase.startMainmenu()
	
	def responseReader(self, task):
		if task.time > 2.5:
			self.loginButton["state"] = DGG.NORMAL
			self.createAccButton["state"] = DGG.NORMAL
			self.updateStatus("Timeout from Login server")
			return task.done
		else:
			temp = self.showbase.authCon.getData()
			for package in temp:
				if len(package) == 2:
					print "Received: " + str(package)
					print "Connected to login server"
					if package[0] == 'loginFailed':
						print "Login failed: ", package[1]
						if package[1] == 'username':
							self.updateStatus("Username Doesnt Exist")
							self.passwordBox.set("")
							self.usernameBox.set("")
							self.passwordBox['focus'] = 0
							self.usernameBox['focus'] = 1
						elif package[1] == 'password':
							self.updateStatus("Password Incorrect")
							self.passwordBox.set("")
							self.usernameBox['focus'] = 0
							self.passwordBox['focus'] = 1
						elif package[1] == 'logged':
							self.updateStatus("Username already logged in")
						self.requestAttempt = False
						self.loginButton["state"] = DGG.NORMAL
						self.createAccButton["state"] = DGG.NORMAL
						return task.done
					elif package[0] == 'loginValid':
						print "Login valid: ", package[1]
						self.updateStatus(package[1])
						self.updateConfig()
						self.showbase.startMainmenu()
						return task.done
					elif package[0] == 'createFailed':
						print "Create failed: ", package[1]
						if package[1] == 'exists':
							self.updateStatus("Username Already Exists")
							self.passwordBox.set("")
							self.usernameBox.set("")
							self.passwordBox['focus'] = 0
							self.usernameBox['focus'] = 1
						self.requestAttempt = False
						self.loginButton["state"] = DGG.NORMAL
						self.createAccButton["state"] = DGG.NORMAL
						return task.done
					elif package[0] == 'createSuccess':
						print "Create success", package[1]
						self.updateStatus("Account Created Successfully")
						self.requestAttempt = False
						self.attemptLogin()
						return task.done
			return task.cont
		
	def cycleLoginBox(self):
		# function is triggered by the tab key so you can cycle between
		# the two input fields like on most login screens
		if self.passwordBox['focus'] == 1:
			self.passwordBox['focus'] = 0
			self.usernameBox['focus'] = 1
		elif self.usernameBox['focus'] == 1:
			self.usernameBox['focus'] = 0
			self.passwordBox['focus'] = 1
		# IMPORTANT: When you change the focus to one of the text boxes,
		# you have to unset the focus on the other textbox.  If you do not
		# do this Panda seems to get confused.
	
	def hide(self):
		self.background.destroy()
		self.usernameText.destroy()
		self.usernameBox.destroy()
		self.usernameStoreBox.destroy()
		self.passwordText.destroy()
		self.passwordBox.destroy()
		self.passwordStoreBox.destroy()
		self.loginButton.destroy()
		self.quitButton.destroy()
		self.createAccButton.destroy()
		self.statusText.destroy()
		
		self.showbase.ignore('tab')
		self.showbase.ignore('shift-tab')
		self.showbase.ignore('enter') 
