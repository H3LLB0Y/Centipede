from pandac.PandaModules import CollisionSphere, CollisionNode, Vec3
	
def initCollisionSphere(obj, desc, radiusMultiplier):
		# Get the size of the object for the collision sphere.
		bounds = obj.getChild(0).getBounds()
		center = bounds.getCenter()
		radius = bounds.getRadius() * radiusMultiplier

		# Create a collision sphere and name it something understandable.
		collSphereStr = desc
		cNode = CollisionNode(collSphereStr)
		cNode.addSolid(CollisionSphere(center, radius))

		cNodepath = obj.attachNewNode(cNode)
		#if show:
		#cNodepath.show()

		# Return a tuple with the collision node and its corrsponding string so
		# that the bitmask can be set.
		return (cNodepath, collSphereStr)
