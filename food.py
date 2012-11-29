from direct.actor.Actor import Actor
from pandac.PandaModules import CollisionSphere, CollisionNode
from util import *

class Food():
	def __init__(self, x, y, h, num, addToCollisions, cTrav, collHandEvent):
		self.addToCollisions = addToCollisions
		self.trav = cTrav
		self.event = collHandEvent
		self.num = num
		
		# Load food model
		self.model = Actor('models/panda-model',
							{'Walk': 'models/panda-walk4'})
		# Set Scale of food
		self.model.setScale(0.00065, 0.00065, 0.00065)
		# Set animation loop to Walk
		self.model.loop('Walk')
		# Reparent the model to render.
		self.model.reparentTo(base.render)
		
		self.model.collisionNode = initCollisionSphere(self.model, 'Food-' + str(num), 0.6)
		
		# Add head to collision detection
		self.addToCollisions(cTrav, collHandEvent, self.model.collisionNode)
		
		self.reset(x, y, h)
		
	def update(self, dt):
		self.model.setPos(self.model, 0, 0.1 * dt, 0)

	def reset(self, x, y, h):
		# Set position of centipede head
		self.model.setX(x)
		self.model.setY(y)
		# Set rotation of centipede head
		self.model.setH(h)
