import errors
import parser
import copy

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
		self.isAvail = True
		# For stats
		self.busyxacts = {}
		self.busyticks = 0 # divided by curticks in the end; 
		                   # this is busyness from 0 to 1 (weighted stat)
		self.unweightedbusyticks = 0 # busyness from 0 to maxplaces
		self.enters_f = 0
		self.processedxactsticks = 0
		self.avail_time = 0
		self.unavail_time = 0
		self.maxxacts = 0
		
class Queue:
	def __init__(self, name):
		self.name = name
		#For stats
		self.queuedxacts = []
		self.enters_q = 0
		self.curxacts = 0
		# Max length
		self.maxxacts = 0
		# Average length of queue (if divided by curticks):
		self.sumforavg = 0 # in the end this will be divided by curticks
		self.zero_entries = 0
		self.sum_for_avg_time_in_queue = 0 # divided by enters or 
		                                   # enters minus zero entries
		self.max_time_in_queue = 0
		
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
		
	def sample(self, value, weight):
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
		
class Graph2D:
	def __init__(self, name, parameters):
		self.paramX = parameters[0]
		self.paramY = parameters[1]
		self.values = {}
		
	def sample(self, x, y):
		if x in self.values.keys():
			self.values[x] = (self.values[x] + y) / 2.0
		else:
			self.values[x] = y

class ConditionalFunction:
	def __init__(self, name, args, choices):
		self.name = name
		self.args = args       # ['arg1', 'arg2']
		self.choices = choices # [[cond1, ret1], [cond2, ret2]]
		
	def call(self, argvalues):
		oldchoices = copy.deepcopy(self.choices)
		oldpos = parser.pos
		oldline = copy.deepcopy(parser.tokline)
		self.replaceArgsWithValues(argvalues)
		for choice in self.choices:
			parser.pos = 0
			parser.tokline = choice[0]
			if parser.parseExpression():
				parser.pos = 0
				parser.tokline = choice[1]
				retval = parser.parseExpression()
				parser.pos = oldpos
				parser.tokline = copy.deepcopy(oldline)
				self.choices = copy.deepcopy(oldchoices)
				return retval
		# If no condition evaluated to true:
		parser.pos = oldpos
		parser.tokline = copy.deepcopy(oldline)
		self.choices = copy.deepcopy(oldchoices)
		return 0
		
	def replaceArgsWithValues(self, values):
		for i in range(len(self.args)):
			if type(values[i]) is int or type(values[i]) is float:
				valuetype = 'number'
			elif type(values[i]) is bool:
				valuetype = 'word'
			elif type(values[i]) is str:
				valuetype = 'string'
				
			for choice in self.choices:
				for expr in choice:
					prevtoken = []
					for token in expr:
						if token[1] == self.args[i] and prevtoken != ['dot', '']:
							token[0] = valuetype
							token[1] = values[i]
						prevtoken = token
