import errors
import parser

class IntVar:
	def __init__(self, name, initval):
		if type(initval) is not int:
			errors.print_error(10, parser.lineindex, [name])
		self.value = initval
		self.name = name
		
class FloatVar:
	def __init__(self, name, initval):
		if type(initval) is not int or type(initval) is not float:
			errors.print_error(11, parser.lineindex, [name])
		self.value = initval
		self.name = name
		
class BoolVar:
	def __init__(self, name, initval):
		if type(initval) is bool:
			self.value = initval
		else:
			errors.print_error(32, parser.lineindex, [name])
		self.name = name
		
class StrVar:
	def __init__(self, name, initval):
		self.value = initval
		self.name = name
		
class Facility:
	def __init__(self, name, places, isQueued):
		self.name = name
		self.maxplaces = places
		self.isQueued = isQueued
		self.curplaces = places
		# For stats
		self.busyxacts = []
		self.busyticks = 0
		self.enters_f = 0
		
class Queue:
	def __init__(self, name):
		self.name = name
		#For stats
		self.queuedxacts = []
		self.enters_q = 0
		self.curxacts = 0
		
class Mark:
	def __init__(self, name, block):
		self.name = name
		self.block = block
		
class Chain:
	def __init__(self, name):
		self.name = name
		self.xacts = []
		self.length = 0
		
class Injector:
	def __init__(self, group, time, tdelta, tdelay, limit, block, params={}):
		self.group = group
		self.time = time
		self.tdelta = tdelta
		self.tdelay = tdelay
		if limit <= 0:
			self.limit = -1
		else:
			self.limit = limit
		self.block = block
		if 'priority' in params.keys():
			self.pr = params['priority']
			del params['priority']
		else:
			self.pr = 0
		self.params = params
