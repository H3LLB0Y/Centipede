from pandac.PandaModules import loadPrcFileData
loadPrcFileData("",
"""
	window-title Centipede!
	fullscreen 0
	win-size 1024 768
	cursor-hidden 0
	sync-video 1
	frame-rate-meter-update-interval 0.5
	show-frame-rate-meter 1
"""
)

from direct.showbase.ShowBase import ShowBase

from login import Login
from mainmenu import MainMenu
from pregame import Pregame
from round import Round

# For starting the server from within the game
from subprocess import Popen
# For exit function
import sys

class Main(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)
		self.login = Login(self)
	
	def startMainmenu(self):
		self.login.hide()
		self.mainmenu = MainMenu(self)
		self.pregame = Pregame(self)
		self.mainmenu.show()
	
	def startPregame(self):
		self.mainmenu.hide()
		self.pregame.reset()
		self.pregame.show()

	def returnToMenu(self):
		self.pregame.hide()
		self.mainmenu.show()
	
	def startRound(self):
		self.pregame.hide()
		self.round = Round(self)
	
	def endRound(self):
		self.round.destroy()
		del self.round
		self.pregame.show()
		
	def hostGame(self, params):
		pid = Popen(["python", "server.py", params]).pid
		print 'Server Process ID:', pid
	
	def quit(self):
		sys.exit()

game = Main()
game.run()
