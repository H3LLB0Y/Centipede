from world							import World
from centipede						import Centipede
from food							import Food
from camerahandler					import CameraHandler
from direct.showbase import DirectObject 
from pandac.PandaModules import *
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
		self.accept("c", self.setValue, [self.keys, "c", 1])
		self.accept("c-up", self.setValue, [self.keys, "c", 0])
		
		# mouse 1 is for casting the spell set by the keys
		#showbase.accept("mouse1", self.castSpell)
		
		# mouse 3 is for movement, or canceling keys for casting spell
		self.accept("mouse3", self.updateDestination)
		
		self.ch = CameraHandler()
		
		# sets the camera up behind clients warlock looking down on it from angle
		follow = self.game.centipede.head
		self.ch.setTarget(follow.getPos().getX(), follow.getPos().getY(), follow.getPos().getZ())
		self.ch.turnCameraAroundPoint(follow.getH(), 0)

	def setValue(self, array, key, value):
		array[key] = value
	
	# sends destination request to server, or cancels spell if selected
	def updateDestination(self):
		destination = self.ch.getMouse3D()
		if not destination.getZ() == -1:
			self.client.sendData(('updateDest', (destination.getX(), destination.getY())))

	def updateCamera(self, dt):
		# sets the camMoveTask to be run every frame
		self.ch.camMoveTask(dt)
		
		# if c is down update camera to always be following on the warlock
		if self.keys["c"]:
			follow = self.game.centipede.head
			self.ch.setTarget(follow.getPos().getX(), follow.getPos().getY(), follow.getPos().getZ())
			self.ch.turnCameraAroundPoint(0, 0)

	def update(self, dt):
		self.updateCamera(dt)
	
	def destroy(self):
		self.ignoreAll()
		self.ch.destroy()

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
				self.centipede.attachRing(showbase)
		
		self.foods = []
		for i in range(self.gameData.maxFoods):
			self.foods.append(Food(self.showbase, i, self.addToCollisions))
		
		self.ticks = 0

	def destroy(self):
		self.world.destroy()
		for user in self.usersData:
			user.centipede.destroy()
		for food in self.foods:
			food.destroy()
		
	def runTick(self, dt):
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
