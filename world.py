# World Class
class World():
	def __init__(self, showbase):
		# Load the environment model (Ground and Surrounding Rocks)
		self.ground = showbase.loader.loadModel('models/world')
		# Scale environment
		self.ground.setScale(100)
		# Reparent the model to render
		self.ground.reparentTo(showbase.render)

	def destroy(self):
		self.ground.detachNode()
