from math import pi, sin, cos, atan2, floor, degrees
from direct.actor.Actor import Actor
from pandac.PandaModules import Vec3, CollisionSphere, CollisionNode
from util import *

# Centipede Class
class Centipede():
	def getH(self):
		# Return heading (rotation) of centipede head
		return self.head.getH()
	
	def getPos(self):
		# Return position of centipede head
		return self.head.getPos()
	
	def rotateLeft(self, dt):
		# Rotate centipede by dt*90.0
		self.head.setH(self.head.getH() + dt * 90.0)
	
	def moveForwards(self, dt, multi):		
		# Update centipede position
		self.head.setPos(self.head, 0, dt * multi * 25, 0)
		
		for i in range(len(self.body)):
			if i == 0:
				# Calculate new heading angle for body part
				self.body[i].headsUp(self.head)
				# Update body position
				self.body[i].setPos(self.body[i], 0, self.body[i].getDistance(self.head) - self.length, 0)
			else:
				# Calculate new heading angle for body part
				self.body[i].headsUp(self.body[i - 1])
				# Update body position
				self.body[i].setPos(self.body[i], 0, self.body[i].getDistance(self.body[i - 1]) - self.length, 0)
		if len(self.body) > 0:
			# Update Tail Heading
			self.tail.headsUp(self.body[len(self.body) - 1])
			# Update body position
			self.tail.setPos(self.tail, 0, self.body[len(self.body) - 1].getDistance(self.tail) - self.length, 0)
		else:
			# Update Tail Heading
			self.tail.headsUp(self.head)
			# Update body position
			self.tail.setPos(self.tail, 0, self.head.getDistance(self.tail) - self.length, 0)

	def addLength(self):
		# Load centipede model
		node = Actor('models/centipede')
		# Set Scale of centipede
		node.setScale(0.1, 0.1, 0.1)
		# Set animation loop to Walk
		node.loop('Walk')
		# Reparent the model to render.
		node.reparentTo(base.render)
		# Set body rotation
		node.setH(self.tail.getH())
		# Set body position
		node.setPos(self.tail.getPos())
		
		node.collisionNode = initCollisionSphere(node, 'Body-' + str(len(self.body)), 0.65)
		
		self.addToCollisions(self.trav, self.event, node.collisionNode)
		
		# Insert into body list
		self.body.append(node)
		# Set tail position
		self.tail.setPos(node, 0, -0.5, 0)
	
	def __init__(self, x, y, h, addToCollisions, trav, collHandEvent):
		self.addToCollisions = addToCollisions
		self.trav = trav
		self.event = collHandEvent
		self.x = x
		self.y = y
		self.h = h
		
		# Load centipede model
		self.head = Actor('models/centipede')
		# Set Scale of centipede
		self.head.setScale(0.1, 0.1, 0.1)
		# Set animation loop to Walk
		self.head.loop('Walk')
		# Reparent the model to render.
		self.head.reparentTo(base.render)
		
		min, max = self.head.getTightBounds()
		self.length = (max - min).getX() * 5
		
		self.head.collisionNode = initCollisionSphere(self.head, 'Head', 0.65)
		
		# Add head to collision detection
		addToCollisions(self.trav, self.event, self.head.collisionNode)
		
		# Load centipede model
		self.tail = Actor('models/centipede')
		# Set Scale of centipede
		self.tail.setScale(0.1, 0.1, 0.1)
		# Set animation loop to Walk
		self.tail.loop('Walk')
		# Reparent the model to render.
		self.tail.reparentTo(base.render)
		
		self.tail.collisionNode = initCollisionSphere(self.tail, 'Tail', 0.65)
		
		# Add tail to collision detection
		addToCollisions(self.trav, self.event, self.tail.collisionNode)
		
		self.reset()

	def reset(self):
		# Set position of centipede head
		self.head.setX(self.x)
		self.head.setY(self.y)
		# Set rotation of centipede head
		self.head.setH(self.h)
		
		self.body = []
		
		# Set tail position
		self.tail.setPos(self.head, 0, -self.length, 0)
