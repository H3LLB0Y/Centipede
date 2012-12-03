from pandac.PandaModules import *
from util import *
from panda3d.bullet import *

# World Class
class World():
	def __init__(self, showbase):
		# Load the environment model (Ground and Surrounding Rocks)
		self.environ = showbase.loader.loadModel('models/world')
		# Scale environment
		self.environ.setScale(100)
		# Reparent the model to render
		self.environ.reparentTo(showbase.render)
