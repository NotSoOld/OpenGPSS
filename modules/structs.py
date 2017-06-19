class IntVar:
	def __init__(self, name, initval):
		self.value = initval
		self.name = name
		
class FloatVar:
	def __init__(self, name, initval):
		self.value = initval
		self.name = name
		
class Facility:
	def __init__(self, name, places, isQueued):
		self.name = name
		self.maxplaces = places
		self.isQueued = isQueued
		self.curplaces = 0
		# For stats
		self.busyxacts = []
		self.busyticks = 0
		
class Queue:
	def __init__(self, name):
		self.name = name
		#For stats
		self.enters = 0
		self.curxacts = 0
		
class Mark:
	def __init__(self, name, block):
		self.name = name
		self.block = block
