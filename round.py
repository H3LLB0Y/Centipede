from game							import Game, GameHandler

from collections import deque

gameTick = 1.0 / 30.0

class Round():
	# Initialisation Function
	def __init__(self, showbase):
		# Initialise Window
		self.showbase = showbase
		
		# total time since start of game, to keep ticks updating on time (rather, not before)
		self.totalTime = 0
		
		# packets queue
		self.incoming = deque()
		
		users = []
		for user in self.showbase.users:
			if user.name == self.showbase.username:
				user.gameData.thisPlayer = True
			users.append(user.gameData)
		self.game = Game(self.showbase, users, self.showbase.gameData)
		self.gameHandler = GameHandler(self.showbase, self.game)
		
		self.tick = 0
		self.tempTick = 0
		
		# Set event handlers for keys		
		#self.showbase.accept("escape", sys.exit)
		
		# send loading completion packet to the game server
		self.showbase.client.sendData(('round', 'sync'))
		
		# Add the game loop procedure to the task manager.
		self.showbase.taskMgr.add(self.gameLoop, 'Game Loop')
	
	def destroy(self):
		self.showbase.taskMgr.remove('Game Loop')
		self.game.destroy()
		self.gameHandler.destroy()
		
	# Game Loop Procedure
	def gameLoop(self, task):
		dt = task.getDt()
		# update total time
		self.totalTime += dt
		# process any incoming network packets
		temp = self.showbase.client.getData()
		for packet in temp:
			# this part puts the next packets onto the end of the queue
			self.incoming.append(packet)
		
		# while there is packets to process
		while len(self.incoming):
			package = self.incoming.popleft()
			if len(package) == 2:
				# if username is sent, assign to client
				if package[0] == 'tick':
					# not sure if this is the best way to do this but yea something to look into for syncing them all preround i guess
					if package[1] == 0:
						self.totalTime = 0
					# check what tick it should be
					self.tempTick = package[1]
					# if this tick needs to be run (if frames are up to the server tick)
					#if self.temp_tick * game_tick <= self.total_time:
						# run tick
					if not self.game.runTick(gameTick):
						print 'Game Over'
						self.showbase.endRound()
						return task.done
					#else:
						# otherwise put packet back on front of list and end frame processing
					#	self.incoming.appendleft(package)
					#	break
				else:
					for user in self.showbase.users:
						if user.name == package[0]:
							user.gameData.processUpdatePacket(package[1])
		
		self.gameHandler.update(dt)
			
		# Return cont to run task again next frame
		return task.cont
