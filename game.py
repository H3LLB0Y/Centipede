from world							import World
from centipede						import Centipede
from food							import Food
from camerahandler					import CameraHandler
from util							import *
from pandac.PandaModules import *
from panda3d.bullet import *
from direct.gui.OnscreenText import OnscreenText
from direct.showbase import DirectObject 
import random

class GameData():
	def __init__(self, isServer = False):
		self.randSeed = 0.0
		self.maxFoods = 100
		
		if isServer:
			self.randSeed = random.random()

	def packageData(self):
		data = []
		data.append(('seed', self.randSeed))
		return data

	def unpackageData(self, data):
		for package in data:
			if package[0] == 'seed':
				self.randSeed = package[1]

class GameHandler(DirectObject.DirectObject):
	def __init__(self, client, game):
		self.client = client
		self.game = game
		
		# Keys array (down if 1, up if 0)
		self.keys = { "left": 0, "right": 0, "up": 0, "down": 0, "c": 0 }
		
		# holding c will focus the camera on clients warlock
		self.accept("c", set_value, [self.keys, "c", 1])
		self.accept("c-up", set_value, [self.keys, "c", 0])
		
		# mouse 1 is for casting the spell set by the keys
		#showbase.accept("mouse1", self.cast_spell)
		
		# mouse 3 is for movement, or canceling keys for casting spell
		self.accept("mouse3", self.update_destination)
		
		self.ch = CameraHandler()
		
		# sets the camera up behind clients warlock looking down on it from angle
		follow = self.game.centipede.head
		self.ch.setTarget(follow.getPos().getX(), follow.getPos().getY(), follow.getPos().getZ())
		self.ch.turnCameraAroundPoint(follow.getH(), 0)
	
	# sends destination request to server, or cancels spell if selected
	def update_destination(self):
		destination = self.ch.get_mouse_3d()
		if not destination.getZ() == -1:
			self.client.sendData(('update_dest', (destination.getX(), destination.getY())))

	def update_camera(self, dt):
		# sets the camMoveTask to be run every frame
		self.ch.camMoveTask(dt)
		
		# if c is down update camera to always be following on the warlock
		if self.keys["c"]:
			follow = self.game.centipede.head
			self.ch.setTarget(follow.getPos().getX(), follow.getPos().getY(), follow.getPos().getZ())
			self.ch.turnCameraAroundPoint(0, 0)

	def update(self, dt):
		self.update_camera(dt)
	
	def destroy(self):
		self.ignoreAll()

class Game(DirectObject.DirectObject):
	def __init__(self, showbase, usersData, gameData):
		self.showbase = showbase
		self.usersData = usersData
		self.gameData = gameData
		
		random.seed(self.gameData.randSeed)
		
		# Initialize the collision traverser.
		self.cTrav = CollisionTraverser()
		
		# Initialize the handler.
		self.collHandEvent = CollisionHandlerEvent()
		self.collHandEvent.addInPattern('into-%in')
		
		self.world = World(showbase)
		
		for user in self.usersData:
			user.centipede = Centipede(showbase, len(self.usersData), self.addToCollisions)
			if user.thisPlayer:
				self.centipede = user.centipede
				self.centipede.attach_ring(showbase)
		
		self.foods = []
		for i in range(self.gameData.maxFoods):
			self.foods.append(Food(i, self.addToCollisions))
		
		self.ticks = 0
		
	def run_tick(self, dt):
		# run each of the centipedes simulations
		for user in self.usersData:
			user.centipede.update(dt)
			if len(user.centipede.body) > 10:
				return False
		
		for food in self.foods:
			food.update(dt)
		
		self.cTrav.traverse(self.showbase.render)
		
		self.ticks += 1
		
		# Return true if game is still not over (false to end game)
		return True

	def collideInto(self, collEntry):
		for user in self.usersData:
			if collEntry.getFromNodePath() == user.centipede.head.collisionNode[0]:
				for food in self.foods:
					if collEntry.getIntoNodePath() == food.model.collisionNode[0]:
						user.centipede.addLength()
						food.reset()
				if len(user.centipede.body) > 2:
					if collEntry.getIntoNodePath() == user.centipede.tail.collisionNode[0]:
						user.centipede.reset()
					for i in range(len(user.centipede.body) - 1 - 2):
						if collEntry.getIntoNodePath() == user.centipede.body[i + 2].collisionNode[0]:
							user.centipede.reset()
							break
	
	def addToCollisions(self, item):
		# Add this object to the traverser.
		self.cTrav.addCollider(item[0], self.collHandEvent)

		# Accept the events sent by the collisions.
		self.accept('into-' + str(item[1]), self.collideInto)
