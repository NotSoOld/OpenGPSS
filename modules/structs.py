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
		self.irruptch = []
		# For stats
		self.busyxacts = {}
		self.busyticks = 0
		self.enters_f = 0
		self.processedxactsticks = 0
		
class Queue:
	def __init__(self, name):
		self.name = name
		#For stats
		self.queuedxacts = []
		self.enters_q = 0
		self.curxacts = 0
		self.maxxacts = 0
		self.sumforavg = 0 # in the end this will be divided by curticks
		
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
		if 'priority' not in params.keys():
			params['priority'] = 0
		self.params = params
		
class Histogram:
	def __init__(self, name, param, startval, interval, count):
		self.name = name
		self.param = param
		self.startval = startval
		self.interval = interval
		self.count = int(count)
		self.intervals = [0 for _ in range(self.count+2)]
		# for stats:
		self.sum = 0
		self.enters_h = 0
		self.average = 0
		
	def add(self, value, weight):
		if value < self.startval:
			self.intervals[0] += weight
		elif value > self.startval + self.interval * self.count:
			self.intervals[-1] += weight
		else:
			for i in range(1, self.count+1):
				l = self.startval + self.interval * (i - 1)
				r = self.startval + self.interval * i
				if l < value < r:
					self.intervals[i] += weight
					break
		self.sum += value * weight
		self.enters_h += weight
		self.average = self.sum / float(self.enters_h)
				
