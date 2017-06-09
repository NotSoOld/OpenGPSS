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
			'reject', 'travel']


class IntVar:
	def __init__(self, name, initValue):
		self.value = initValue
		self.name = name

class FloatVar:
	def __init__(self, name, initValue):
		self.value = initValue
		self.name = name
		
class Facility:
	busyxacts = []
	def __init__(self, name, mode):
		self.name = name
		self.mode = mode
		if mode == 'single':
			self.places = 1
		
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
		if 'fbusy' in line[1] or 'ffree' in line[1]:
			line[1] = line[1].replace(name, strname)
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
		if 'qenter' in line[1] or 'qleave' in line[1]:
			line[1] = line[1].replace(name, strname)
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

def entry(cond, i, j, k):
	cond = (cond.replace('||', ' or ').replace('&&', ' and ')
				.replace('1', '%1%').replace('2', '%2%')
				.replace('3', '%3%'))
	cond = (cond.replace('%1%', 'injected >= '+str(i))
				.replace('%2%', 'rejected >= '+str(j))
				.replace('%3%', 'curticks >= '+str(k)))
	global exitCond
	exitCond = cond
	
def inject(group, time, tdelta, tdelay, limit, block):
	global injectors
	injectors[group] = Injector(group, time, tdelta, tdelay, limit, block)
	
def addMarkedBlock(name, index):
	if name not in marks:
		print('ERROR in line', index, '!! Mark "',
				name, '" is undefined.')
		sys.exit()
	if marks[name].block != -1:
		print('ERROR in line', index, '!! Mark "',
				name, '" is used more than once')
		sys.exit()
	marks[name].block = index
	
def qenter(xact, qid):
	queues[qid].enters += 1
	queues[qid].curxacts += 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def qleave(xact, qid):
	queues[qid].curxacts -= 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def fbusy(xact, fid):
	if facilities[fid].places > 0:
		facilities[fid].places -= 1
		xact.curblk += 1
		facilities[fid].busyxacts.append(xact)
		xact.cond = 'canmove'
	else:
		xact.cond = 'blocked'
	
def ffree(xact, fid):
	facilities[fid].places += 1
	facilities[fid].busyxacts.remove(xact)
	xact.curblk += 1
	xact.cond = 'passagain'
	
def wait(xact, time, tdelta):
	global futureChain
	global curticks
	futime = curticks + time + random.randint(-tdelta, tdelta)
	xact.curblk += 1
	xact.cond = 'waiting'
	print 'exit time =', futime
	futureChain.append([futime, xact])
	
def reject(xact, decr):
	global rejected
	rejected += decr
	xact.curblk += 1
	xact.cond = 'rejected'
	
def travel(xact, truemark, prob=None, addmark=None):
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
	
###############################################################

progfile = open('prog1.ogps', 'r')
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
	line[1] = line[1].replace('\r', '').replace('\n', '')
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
	if program[j][1].startswith('entry'):
		eval(program[j][1])
		
for j in range(i, len(program)):
	t = program[j][1].partition(':')
	if t[0] != '' and t[1] != '':
		addMarkedBlock(t[0], program[j][0])
	if t[2].startswith('inject'):
		tt = t[2].partition(')')
		args = tt[0]
		args += ', '
		args += str(j)
		args += ')'
		eval(args)
	if t[2].partition('(')[0] in commands:
		tup = t[2].partition('(')
		newline = tup[0]+'(xact, '+tup[2]
		program[j][1] = t[0]+':'+newline
		
for ll in program:
	print ll[1]
print(exitCond)
while True:
	tempCurrentChain = []
	ttt = raw_input()
	print 'timestep =', curticks
	print 'Future Events Chain: ', list(xa[0] for xa in futureChain)
	for xa in futureChain:
		if xa[0] == curticks:
			currentChain.append(xa[1])
			# Inject new xact if we move injected xact from future events chain.
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
	if len(currentChain) == 0:
		curticks += 1
		continue
	print 'Current Events Chain:', list(xa.index for xa in currentChain)
	restart = True
	while restart:
		restart = False
		for xact in currentChain:
			if restart:
				tempCurrentChain.append(xact)
				continue
			while True:
				t = program[xact.curblk+1][1].partition(':')[2]
				eval(t)
				print 'xact', xact.index, 'entered block', t
				
				if xact.cond != 'canmove':
					if xact.cond == 'passagain':
						tempCurrentChain.append(xact)
						restart = True
					elif xact.cond == 'blocked':
						tempCurrentChain.append(xact)
						print 'xact', xact.index, 'was blocked'
					break
			#print 'CurEvents Chain:', list(xa.index for xa in currentChain)
			#print 'CurTempEv Chain:', list(xa.index for xa in tempCurrentChain)
			#ttt = raw_input()
			# Stop by rejecting enough xacts.
			if eval(exitCond) == True:
				break
		currentChain = tempCurrentChain
		tempCurrentChain = []
	curticks += 1
	# Stop by modelling enough amount of time.
	if eval(exitCond) == True:
		break
			
print(facilities)
print(queues)
print(marks)
print(exitCond)
for xact in futureChain:
	print(xact[0], xact[1].group, xact[1].index, 
				   xact[1].curblk, xact[1].cond)
for xact in currentChain:
	print xact.group, xact.index, xact.curblk, xact.cond
