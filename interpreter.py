import sys
import random

intVars = {}
floatVars = {}
chains = {}
facilities = {}
queues = {}
marks = {}
injectors = {}
currentChain = []
tempCurrentChain = []
futureChain = []
program = []
injected = 0
rejected = 0
curticks = 0
commands = ['cond', 'fbusy', 'ffree', 
            'wait', 'qenter', 'qleave',
            'reject', 'travel', 'otherwise']
xact = None


class IntVar:
	def __init__(self, name, initValue):
		self.value = initValue
		self.name = name
	
	def assign(self, val):
		self.value = val
		xact.curblk += 1
		xact.cond = 'canmove'
		
	def add(self, val):
		self.assign(self.value + val)
	
	def subt(self, val):
		self.assign(self.value - val)
		
	def mult(self, val):
		self.assign(self.value * val)
		
	def div(self, val):
		self.assign(self.value / val)
		
	def exp(self, val):
		self.assign(self.value ** val)

class FloatVar:
	def __init__(self, name, initValue):
		self.value = initValue
		self.name = name
		
	def assign(self, val):
		self.value = val
		xact.curblk += 1
		xact.cond = 'canmove'
		
	def add(self, val):
		self.assign(self.value + val)
	
	def subt(self, val):
		self.assign(self.value - val)
		
	def mult(self, val):
		self.assign(self.value * val)
		
	def div(self, val):
		self.assign(self.value / val)
		
	def exp(self, val):
		self.assign(self.value ** val)
		
class Facility:
	busyxacts = []
	def __init__(self, name, mode, params={}):
		self.name = name
		self.mode = mode
		if mode == 'single':
			self.places = 1
		else:
			self.places = 1
			#self.places = params['entries']
		
class Queue:
	enters = 0
	curxacts = 0
	def __init__(self, name):
		self.name = name
		
class Mark:
	def __init__(self, name, block):
		self.name = name
		self.block = block
		
class Xact:
	def __init__(self, group, index, curblk):
		self.group = group
		self.index = index
		self.curblk = curblk
		self.cond = 'injected'
		
class Injector:
	def __init__(self, group, time, tdelta, tdelay, limit, block):
		self.group = group
		self.time = time
		self.tdelta = tdelta
		self.tdelay = tdelay
		if limit <= 0:
			self.limit = -1
		else:
			self.limit = limit
		self.block = block
		self.inject()
	
	def inject(self):
		# Limit should be checked before calling this.
		global futureChain
		global curxact
		global curticks
		global injected
		xa = Xact(self.group, injected, self.block)
		injected += 1
		if self.limit != -1:
			self.limit -= 1
		futime = curticks + self.time + random.randint(-self.tdelta, self.tdelta)
		if self.tdelay != 0:
			futime += self.tdelay
			self.tdelay = 0
		futureChain.append([futime, xa])

def addFacility(argstr):
	fd = {}
	t = argstr.partition('(')
	name = t[0]
	mode = t[2].partition(')')[0].replace('\"', '')
	f = Facility(name, mode)
	fd[name] = f
	global program
	strname = '\''+name+'\''
	for line in program:
		tmp = line[1].partition(':')
		if 'fbusy' in tmp[2] or 'ffree' in tmp[2]:
			line[1] = tmp[0] + tmp[1] + tmp[2].replace(name, strname)
	return fd
	
def addQueue(argstr):
	qd = {}
	t = argstr.partition('{')
	name = t[0]
	q = Queue(name)
	qd[name] = q
	global program
	strname = '\''+name+'\''
	for line in program:
		tmp = line[1].partition(':')
		if 'qenter' in tmp[2] or 'qleave' in tmp[2]:
			line[1] = tmp[0] + tmp[1] + tmp[2].replace(name, strname)
	return qd
	
def addMark(argstr):
	md = {}
	name = argstr.partition(';')[0]
	m = Mark(name, -1)
	md[name] = m
	global program
	strname = '\''+name+'\''
	for line in program:
		if 'travel' in line[1]:
			line[1] = line[1].replace(name, strname)
	return md
	
def addInt(name, initval):
	global program
	for line in program:
		parsedname = ''
		if line[1].startswith('exitwhen'):
			text = ('', '', line[1])
		else:
			text = line[1].partition(':')
		if name+'.' in text[2]:
			parsedname = 'intVars[\''+name+'\']'
		elif name in text[2]:
			parsedname = 'intVars[\''+name+'\'].value'
		newtext = text[2].replace(name, parsedname)
		line[1] = text[0] + text[1] + newtext
	return {name:IntVar(name, initval)}
	
def addFloat(name, initval):
	global program
	for line in program:
		parsedname = ''
		if line[1].startswith('exitwhen'):
			text = ('', '', line[1])
		else:
			text = line[1].partition(':')
		if name+'.' in text[2]:
			parsedname = 'floatVars[\''+name+'\']'
		elif name in text[2]:
			parsedname = 'floatVars[\''+name+'\'].value'
		newtext = text[2].replace(name, parsedname)
		line[1] = text[0] + text[1] + newtext
		print line[1]
	return {name:FloatVar(name, initval)}

def exitwhen(cond):
	global exitCond
	exitCond = cond
	
def inject(group, time, tdelta, tdelay, limit, block):
	global injectors
	injectors[group] = Injector(group, time, tdelta, tdelay, limit, block)
	
def addMarkedBlock(name, index):
	if name not in marks:
		print 'ERROR in line', index, '!! Mark "', \
				name, '" is undefined.'
		sys.exit()
	if marks[name].block != -1:
		print 'ERROR in line', index, '!! Mark "', \
				name, '" is used more than once'
		sys.exit()
	marks[name].block = index
	
def qenter(qid):
	queues[qid].enters += 1
	queues[qid].curxacts += 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def qleave(qid):
	queues[qid].curxacts -= 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def fbusy(fid):
	if facilities[fid].places > 0:
		facilities[fid].places -= 1
		xact.curblk += 1
		facilities[fid].busyxacts.append(xact)
		xact.cond = 'canmove'
	else:
		xact.cond = 'blocked'
	
def ffree(fid):
	facilities[fid].places += 1
	facilities[fid].busyxacts.remove(xact)
	xact.curblk += 1
	xact.cond = 'passagain'
	
def wait(time, tdelta):
	global futureChain
	global curticks
	futime = curticks + time + random.randint(-tdelta, tdelta)
	xact.curblk += 1
	xact.cond = 'waiting'
	print 'exit time =', futime
	futureChain.append([futime, xact])
	
def reject(decr):
	global rejected
	rejected += decr
	xact.curblk += 1
	xact.cond = 'rejected'
	
def travel(truemark, prob=None, addmark=None):
	xact.cond = 'canmove'
	if prob != None:
		if random.random() < prob:
			xact.curblk = marks[truemark].block - 1
		else:
			if addmark != None:
				xact.curblk = marks[addmark].block - 1
			else:
				xact.curblk += 1
	else:
		xact.curblk = marks[truemark].block - 1
		
def cond(condition):
	print condition+' is '+str(eval(condition))
	if eval(condition):
		xact.curblk += 1
		xact.cond = 'canmove'
		return
		
	global program
	depth = 0
	for i in range(xact.curblk+2, len(program)):
		if program[i][1].startswith('{'):
			depth += 1
		if program[i][1].startswith('}'):
			depth -= 1
		if depth == 0:
			break
	# Here i == index of line with '}: [otherwise(tryagain)]'
	# or simply with closing bracket.
	
	# We can be here only if condition == False.
	# If it is just conditional 'jump' or non-blocking cond:
	if not 'tryagain' in program[i][1]:
		xact.curblk = i - 1
		xact.cond = 'canmove'
	# If this cond has an blocking otherwise option:
	else:
		xact.cond = 'blocked'
			
def otherwise(cond=None):
	global program
	# We don't need to manage blocking 'tryagain' option here,
	# because cond() does it already.
	if 'tryagain' in program[xact.curblk+1][1]:
		xact.curblk += 1
		xact.cond = 'canmove'
		return
	
	# Just like 'else' with no condition 
	# (and true condition also goes here).
	if cond == None or cond:
		xact.curblk += 1
		xact.cond = 'canmove'
	else:
		depth = 0
		for i in range(xact.curblk+2, len(program)):
			if program[i][1].startswith('{'):
				depth += 1
			if program[i][1].startswith('}'):
				depth -= 1
			if depth == 0:
				break
		xact.curblk = i - 1
		xact.cond = 'canmove'

	
###############################################################


progfile = open('prog2.ogps', 'r')
allprogram = progfile.read()
progpart = allprogram.partition('/*')
while progpart[1] != '':
	allprogram = progpart[0] + progpart[2].partition('*/')[2]
	progpart = allprogram.partition('/*')
temp = allprogram.split(';')
i = 0
for line in temp:
	program.append([i, line])
	i += 1
progfile.close()

i = 0
flag = 0
for line in program:
	line[1] = line[1].replace('\r', '').replace('\n', '').replace('\t', ' ')
for line in program:
	if line[1].find('{{') != -1:
		flag = 1
		line[1] = line[1].replace('{{', '')
		break
	i += 1
for j in range(i):
	t = program[j][1].partition(' ')
	cmd = t[0]
	args = t[2]
	if cmd == 'facility':
		facilities.update(addFacility(args))
	elif cmd == 'queue':
		queues.update(addQueue(args))
	elif cmd == 'mark':
		marks.update(addMark(args))
	elif cmd == 'int':
		intargs = args.replace(' ', '').partition('=')
		if intargs[1] != '':
			intVars.update(addInt(intargs[0], int(intargs[2])))
		else:
			intVars.update(addInt(intargs[0], 0))
	elif cmd == 'float':
		floatargs = args.replace(' ', '').partition('=')
		if floatargs[1] != '':
			floatVars.update(addFloat(floatargs[0], float(floatargs[2])))
		else:
			floatVars.update(addFloat(floatargs[0], 0))
	if program[j][1].startswith('exitwhen'):
		tup2 = program[j][1].partition('(')
		newstr = tup2[0] + '(\"' + tup2[2]
		tup2 = newstr.partition(')')
		newstr = tup2[0] + '\")' + tup2[2]
		program[j][1] = newstr
		eval(program[j][1])
		
for j in range(i, len(program)):
	program[j][1] = program[j][1].replace(' ', '')
	t = program[j][1].partition(':')
	if t[0] != '' and t[0] != '{' and t[0] != '}' and t[1] != '':
		addMarkedBlock(t[0], program[j][0])
	if t[2].startswith('inject'):
		tt = t[2].partition(')')
		args = tt[0]
		args += ', '
		args += str(j)
		args += ')'
		eval(args)
	if t[2].startswith('cond') or t[2].startswith('otherwise'):
		tup = t[2].partition('(')
		newline = tup[0]+'(\"'+tup[2]
		tup = newline.partition(')')
		newline = tup[0]+'\")'+tup[2]
		program[j][1] = t[0]+':'+newline
		
for ll in program:
	print str(ll[0]).zfill(3)+'\t'+ll[1]
inp = raw_input()
while True:
	tempCurrentChain = []
#	inp = raw_input()
	print 'timestep =', curticks
	for xa in futureChain:
		if xa[0] == curticks:
			currentChain.append(xa[1])
			# Inject new xact if we move injected xact 
			# from future events chain.
			if xa[1].cond == 'injected':
				if injectors[xa[1].group].limit != 0:
					injectors[xa[1].group].inject()
			# Mark for future deleting (because now we don't want 
			# to modify collection we're iterating)
			xa[0] = -1
			# Stop by injecting enough xacts.
			if eval(exitCond) == True:
				break
	futureChain = [xa for xa in futureChain if xa[0] != -1]
	print 'Future Events Chain: ', list(xa[0] for xa in futureChain)
	print 'Current Events Chain:', list(xa.index for xa in currentChain)
	if len(currentChain) == 0:
		curticks += 1
		continue
	restart = True
	while restart:
		restart = False
		for xact in currentChain:
			if restart:
				tempCurrentChain.append(xact)
				continue
			while True:
				t = program[xact.curblk+1][1].partition(':')[2]
				print 'xact', xact.index, 'entered block', t
				eval(t)
				
				if xact.cond != 'canmove':
					if xact.cond == 'passagain':
						tempCurrentChain.append(xact)
						restart = True
					elif xact.cond == 'blocked':
						tempCurrentChain.append(xact)
						print 'xact', xact.index, 'was blocked'
					break
			# Stop by rejecting enough xacts.
			if eval(exitCond) == True:
				break
		currentChain = tempCurrentChain
		tempCurrentChain = []
	curticks += 1
	# Stop by modelling enough amount of time.
	if eval(exitCond) == True:
		break

print 'Variables:'
for intt in intVars.keys():
	print str(intt)+' = '+str(intVars[intt].value)
print 'Facilities:'
for fac in facilities.values():
	print fac.name+', '+fac.mode
	l = []
	for xact in fac.busyxacts:
		l.append(xact.index)
	print l
print 'Marks:'
for mark in marks.keys():
	print marks[mark].name, marks[mark].block
print 'Exit condition: '+exitCond
print 'Future events chain:'
for xact in futureChain:
	print xact[0], xact[1].group, xact[1].index, \
				   xact[1].curblk, xact[1].cond
print 'Current events chain:'
for xact in currentChain:
	print xact.group, xact.index, xact.curblk, xact.cond
