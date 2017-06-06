import sys
import random

intVars = {}
floatVars = {}
chains = {}
facilities = {}
queues = {}
marks = {}
injectors = {}
presentChain = []
futureChain = {}
program = []
injected = 0
rejected = 0
tickLim = 0
curticks = 0
curxact = 0


class IntVar:
    def __init__(self, name, initValue):
        self.value = initValue
        self.name = name

class FloatVar:
    def __init__(self, name, initValue):
        self.value = initValue
        self.name = name
        
class Facility:
    def __init__(self, name, mode):
        self.name = name
        self.mode = mode
        
class Queue:
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
		xa = Xact(self.group, curxact, self.block)
		curxact += 1
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
    return fd
    
def addQueue(argstr):
    qd = {}
    t = argstr.partition('{')
    name = t[0]
    q = Queue(name)
    qd[name] = q
    return qd
    
def addMark(argstr):
	md = {}
	name = argstr.partition(';')[0]
	m = Mark(name, -1)
	md[name] = m
	return md

def entry(cond, i, j, k):
    cond = cond.replace('||', ' or ').replace('&&', ' and ').replace('1', '%1%').replace('2', '%2%').replace('3', '%3%')
    cond = cond.replace('%1%', 'injected >= '+str(i)).replace('%2%', 'rejected >= '+str(j)).replace('%3%', 'tickLim >= '+str(k))
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
print(program)
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
		
while 1 == 1:
	for k in futureChain.keys():
		if k == curticks:
			presentChain.append(futureChain[k])
			if futureChain[k].cond == 'injected':
				if injectors[futureChain[k].group].limit != 0:
					injectors[futureChain[k].group].inject()
			del futureChain[k]
	for xact in presentChain:
		t = program[xact.curblk+1][1].partition(':')[2]
		t1 = t.partition(')')[0]
		t1 += ', xact)'
		t1 += t.partition(')')[2]
		eval(t1)
	
	curticks += 1
		
print(facilities)
print(queues)
print(marks)
print(exitCond)
for xact in futureChain:
	print xact, futureChain[xact].group, futureChain[xact].index, futureChain[xact].curblk
