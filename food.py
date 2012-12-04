from direct.actor.Actor import Actor
from collision import initCollisionSphere
import random

class Food():
	def __init__(self, showbase, num, addToCollisions):
		self.addToCollisions = addToCollisions
		self.num = num
		
		# Load food model
		self.model = Actor('panda-model',
							{'Walk': 'models/panda-walk4'})
		# Set Scale of food
		self.model.setScale(0.0065, 0.0065, 0.0065)
		# Set animation loop to Walk
		self.model.loop('Walk')
		# Reparent the model to render.
		self.model.reparentTo(showbase.render)
		
		self.model.collisionNode = initCollisionSphere(self.model, 'Food-' + str(num), 0.6)
		
		# Add head to collision detection
		self.addToCollisions(self.model.collisionNode)
		
		self.reset()

	def destroy(self):
		self.model.detachNode()
		
	def update(self, dt):
		self.model.setPos(self.model, 0, 0.1 * dt, 0)

	def reset(self):
		# Set position of centipede head
		self.model.setX(random.random() * 1000 - 500)
		self.model.setY(random.random() * 1000 - 500)
		# Set rotation of centipede head
		self.model.setH(random.random() * 360)
