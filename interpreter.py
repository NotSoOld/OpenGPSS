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
futureChain = {}
program = []
injected = 0
rejected = 0
curticks = 0


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
		futureChain[futime] = xa

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
	return md

def entry(cond, i, j, k):
	cond = cond.replace('||', ' or ').replace('&&', ' and ').replace('1', '%1%').replace('2', '%2%').replace('3', '%3%')
	cond = cond.replace('%1%', 'injected >= '+str(i)).replace('%2%', 'rejected >= '+str(j)).replace('%3%', 'curticks >= '+str(k))
	global exitCond
	exitCond = cond
	
def inject(group, time, tdelta, tdelay, limit, block):
	global injectors
	injectors[group] = Injector(group, time, tdelta, tdelay, limit, block)
	
def addMarkedBlock(name, index):
	if name not in marks:
		print 'ERROR in line', index, '!! Mark "', name, '" is undefined.'
		sys.exit()
	if marks[name].block != -1:
		print 'ERROR in line', index, '!! Mark "', name, '" is used more than once'
		sys.exit()
	marks[name].block = index
	
def qenter(qid, xact):
	queues[qid].enters += 1
	queues[qid].curxacts += 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def qleave(qid, xact):
	queues[qid].curxacts -= 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def fbusy(fid, xact):
	if facilities[fid].places > 0:
		facilities[fid].places -= 1
		xact.curblk += 1
		facilities[fid].busyxacts.append(xact)
		xact.cond = 'canmove'
	else:
		xact.cond = 'blocked'
	
def ffree(fid, xact):
	facilities[fid].places += 1
	facilities[fid].busyxacts.remove(xact)
	xact.curblk += 1
	xact.cond = 'passagain'
	
def wait(time, tdelta, xact):
	global futureChain
	global curticks
	futime = curticks + time + random.randint(-tdelta, tdelta)
	xact.curblk += 1
	xact.cond = 'waiting'
	print 'exit time =', futime
	futureChain[futime] = xact
	
def reject(decr, xact):
	global rejected
	rejected += decr
	xact.curblk += 1
	xact.cond = 'rejected'
	
###############################################################

progfile = open('prog1.gwls', 'r')
allprogram = progfile.read()
temp = allprogram.split(';')
i = 0
for line in temp:
	l = []
	l.append(i)
	l.append(line)
	program.append(l)
	i += 1
progfile.close()
i = 0
flag = 0
for line in program:
	line[1] = line[1].replace('\r\n', '')
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

print(program)
		
for j in range(i,len(program)):
	t = program[j][1].partition(':')
	if t[0] != '' and t[1] != '':
		addMarkedBlock(t[0],program[j][0])
	if t[2].startswith('inject'):
		tt = t[2].partition(')')
		args = tt[0]
		args += ', '
		args += str(j)
		args += ')'
		eval(args)
		
print(exitCond)
while True:
	tempCurrentChain = []
	ttt = raw_input()
	print 'timestep =', curticks
	print 'Future Events Chain: ', list(xa for xa in futureChain.keys())
	for k in futureChain.keys():
		if k == curticks:
			currentChain.append(futureChain[k])
			# Inject new xact if we move injected xact from future events chain.
			if futureChain[k].cond == 'injected':
				if injectors[futureChain[k].group].limit != 0:
					injectors[futureChain[k].group].inject()
			del futureChain[k]
			# Stop by injecting enough xacts.
			if eval(exitCond) == True:
				break
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
				t1 = t.partition(')')[0]
				t1 += ', xact)'
				t1 += t.partition(')')[2]
				eval(t1)
				print 'xact', xact.index, 'entered block', t1
				
				if xact.cond != 'canmove':
					if xact.cond == 'passagain':
						tempCurrentChain.append(xact)
						restart = True
					elif xact.cond == 'blocked':
						tempCurrentChain.append(xact)
						print 'xact', xact.index, 'was blocked'
					break
			print 'CurEvents Chain:', list(xa.index for xa in currentChain)
			print 'CurTempEv Chain:', list(xa.index for xa in tempCurrentChain)
			ttt = raw_input()
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
	print xact, futureChain[xact].group, futureChain[xact].index, futureChain[xact].curblk, futureChain[xact].cond
for xact in currentChain:
	print xact.group, xact.index, xact.curblk, xact.cond
