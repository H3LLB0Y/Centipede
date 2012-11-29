from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
import sys, random
from centipede import Centipede
from food import Food
from pandac.PandaModules import CollisionTraverser, CollisionHandlerEvent, WindowProperties
from pandac.PandaModules import *

NUM_FOODS = 100

class Game(ShowBase):
	# mouse x movement tracking variable
	mouse_x_change = 0
	# mouse y movement tracking variable
	mouse_y_change = 0

	# Procedure for setting keys
	def setKey(self, key, value):
		# Set key to value
		self.keys[key] = value
	
	# Update Camera Procedue (Movement and Target)
	def updateCamera(self):		
		# Set camera Position
		self.camera.setPos(self.centipede.head, 0, -150, 75)
		# Set camera Rotation
		self.camera.setH(self.centipede.getH())
		
		# If Mouse is available
		if base.mouseWatcherNode.hasMouse():
			# Get X change
			self.mouse_x_change += base.mouseWatcherNode.getMouseX()
			# Limit X change
			if self.mouse_x_change > 1.0:
				self.mouse_x_change = 1.0
			if self.mouse_x_change < -1.0:
				self.mouse_x_change = -1.0
			
			# Get Y change
			self.mouse_y_change += base.mouseWatcherNode.getMouseY()
			# Limit Y change
			if self.mouse_y_change > -1.5:
				self.mouse_y_change = -1.5
			if self.mouse_y_change < -2.5:
				self.mouse_y_change = -2.5
			
			# Set camera Rotation
			self.camera.setH(self.camera.getH() - self.mouse_x_change * 10)
			# Set camera Up/Down Rotation
			self.camera.setP(self.mouse_y_change * 10)
		
		# Set mouse to center of screen
		base.win.movePointer(0, base.win.getXSize() / 2, base.win.getYSize() / 2)
		
		self.mouseRing.setPos(self.centipede.head, self.mouse_x_change * 20, (self.mouse_y_change + 1.5) * 20, 0)
	
	# Game Loop Procedure
	def gameLoop(self, task):
		# get frame delta time
		dt = globalClock.getDt()
		
		for food in self.foods:
			food.update(dt)
		
		# If left or right keys are pressed
		if self.keys['left'] ^ self.keys['right']:
			# If Left key, rotate centipede left
			if self.keys['left']:
				self.centipede.rotateLeft(dt)
			# If Right key, rotate centipede right
			if self.keys['right']:
				self.centipede.rotateLeft(-dt)
		
		# If up or down keys are pressed
		if self.keys['up'] ^ self.keys['down']:
			# If Up key, Move centipede faster
			if self.keys['up']:
				self.centipede.moveForwards(dt, 1.5)
			# If Down key, Move centipede slower
			if self.keys['down']:
				self.centipede.moveForwards(dt, 0.5)
		# Move centipede normal speed
		else:
			self.centipede.moveForwards(dt, 1.0)
		
		# Call update camera procedure
		self.updateCamera()
		
		self.updateScore(len(self.centipede.body))
		
		# Return cont to run task again next frame
		return task.cont

	def collideInto(self, collEntry):
		if collEntry.getFromNodePath() == self.centipede.head.collisionNode[0]:
			#print collEntry.getIntoNodePath()
			for food in self.foods:
				if collEntry.getIntoNodePath() == food.model.collisionNode[0]:
					self.centipede.addLength()
					food.reset(random.random() * 100 - 50, random.random() * 100 - 50, random.random() * 360)
			if len(self.centipede.body) > 15:
				if collEntry.getIntoNodePath() == self.centipede.tail.collisionNode[0]:
					self.centipede.reset()
				for i in range(len(self.centipede.body) - 1 - 15):
					if collEntry.getIntoNodePath() == self.centipede.body[i + 15].collisionNode[0]:
						print collEntry.getIntoNodePath()
						self.centipede.reset()
						break
	
	def addToCollisions(self, trav, event, item):
		# Add this object to the traverser.
		trav.addCollider(item[0], event)

		# Accept the events sent by the collisions.
		self.accept('into-' + str(item[1]), self.collideInto)
	
	def updateScore(self,score):
		self.score.setText('Score: ' + str(score))
	
	# Initialisation Function
	def __init__(self):
		# Initialise Window
		ShowBase.__init__(self)
		
		# Disable Mouse Control for camera
		base.disableMouse()
		# Center Mouse so camera movement can be calculated
		base.win.movePointer(0, base.win.getXSize() / 2, base.win.getYSize() / 2)
		
		# Get windows properties
		props = WindowProperties()
		# Set Hide Cursor Property
		props.setCursorHidden(True)
		# Set properties
		base.win.requestProperties(props)
		
		# Add the game loop procedure to the task manager.
		self.taskMgr.add(self.gameLoop, 'Game Loop')
		
		# Keys array (down if 1, up if 0)
		self.keys = {'left': 0, 'right': 0, 'up': 0, 'down': 0}
		
		# Load the environment model (Ground and Surrounding Rocks)
		self.environ = self.loader.loadModel('models/world')
		# Scale environment
		self.environ.setScale(10)
		# Reparent the model to render
		self.environ.reparentTo(self.render)
		
		# Initialize the collision traverser.
		base.cTrav = CollisionTraverser()
		
		# Initialize the handler.
		self.collHandEvent = CollisionHandlerEvent()
		self.collHandEvent.addInPattern('into-%in')
		
		self.centipede = Centipede(0, 0, 0, self.addToCollisions, base.cTrav, self.collHandEvent)
		
		self.foods = []
		for i in range(NUM_FOODS):
			self.foods.append(Food(random.random() * 100 - 50, random.random() * 100 - 50, random.random() * 360, i, self.addToCollisions, base.cTrav, self.collHandEvent))
		
		self.score = OnscreenText(
			text  = 'Score: 0',
			style = 1,
			fg    = (1, 1, 1, 1),
			pos   = (0, 0.90),
			align = TextNode.ACenter,
			scale = .07
		)
	
		# Set event handlers for keys		
		self.accept('escape', sys.exit)
		# 'h' to add length to centipede
		self.accept('h', self.centipede.addLength)
		# Using WASD Keys
		self.accept('a', self.setKey, ['left', 1])
		self.accept('d', self.setKey, ['right', 1])
		self.accept('w', self.setKey, ['up', 1])
		self.accept('s', self.setKey, ['down', 1])
		self.accept('a-up', self.setKey, ['left', 0])
		self.accept('d-up', self.setKey, ['right', 0])
		self.accept('w-up', self.setKey, ['up', 0])
		self.accept('s-up', self.setKey, ['down', 0])
		
		self.mouseRing = loader.loadModel('models/ring.egg')
		self.mouseRing.reparentTo(base.render)

game = Game()
game.run()
