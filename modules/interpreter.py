import sys
import random
import lexer
import parser
import structs
import errors

ints = {}
floats = {}
strs = {}
chains = {}
facilities = {}
queues = {}
marks = {}
injectors = {}
currentChain = []
tempCurrentChain = []
futureChain = []
injected = 0
rejected = 0
curticks = 0
xact = None
toklines = []
exitcond = -1
		
class Xact:
	def __init__(self, group, index, curblk):
		self.group = group
		self.index = index
		self.curblk = curblk
		self.cond = 'injected'
	
def inject(injector):
	# Limit should be checked before calling this.
	global futureChain
	global curxact
	global curticks
	global injected
	xa = Xact(injector.group, injected, injector.block)
	injected += 1
	if injector.limit != -1:
		injector.limit -= 1
	futime = curticks + injector.time + random.randint(-injector.tdelta, injector.tdelta)
	if injector.tdelay != 0:
		futime += injector.tdelay
		injector.tdelay = 0
	futureChain.append([futime, xa])

	
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
		facilities[fid].enters += 1
		xact.curblk += 1
		facilities[fid].busyxacts.append(xact)
		print 'added xact '+str(xact.index)+' to facility '+fid
		xact.cond = 'canmove'
	else:
		xact.cond = 'blocked'
	
def ffree(fid):
	facilities[fid].places += 1
	facilities[fid].busyxacts = [xa for xa in facilities[fid].busyxacts if xa.index != xact.index]
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

def move(args):
	xact.curblk += 1
	xact.cond = 'canmove'		

	
###############################################################


def start_interpreter(filepath):
	progfile = open(filepath, 'r')
	allprogram = progfile.read()
	progfile.close()

	tokens = lexer.analyze(allprogram)
	for token in tokens:
		print token
	
	global toklines
	toklines = parser.tocodelines(tokens)
	
	skip = False
	for line in toklines:
		if line == [['{{']]:
			skip = True
		elif line == [['}}']]:
			skip = False
		if skip == True:
			continue
		if line[0][0] == 'typedef':
			defd = parser.parseDefinition(line)
			dic = getattr(self, defd[0]+'s')
			if dic[defd[1]]:
				pass #error: multiple definition of name defd[1] with type defd[0]
			dic[defd[1]] = defd[2]
			if defd[0] == 'facilitie' and defd[2].isQueued:
				queues[defd[1]] = structs.Queue(defd[1])
		elif line[0][0] == 'block': 
			if line[0][1] == 'exitwhen':
				if exitcond != -1:
					pass #error: exit condition must be declared only once
				exitcond = toklines.indexof(line)
			else:
				pass #errors.print_error(): executive block outside executive area
	
	for line in toklines:
		if line.indexof(['block', 'inject']) != -1:
			newinj = parser.parseInjector(line)
			injectors[newinj.group] = newinj
			inject(newinj)
			
	while True:
		tempCurrentChain = []
		#inp = raw_input()
		print 'timestep =', curticks
		for xa in futureChain:
			if xa[0] == curticks:
				currentChain.append(xa[1])
				# Inject new xact if we move injected xact 
				# from future events chain.
				if xa[1].cond == 'injected':
					if injectors[xa[1].group].limit != 0:
						inject(injectors[xa[1].group])
				# Mark for future deleting (because now we don't want 
				# to modify collection we're iterating)
				xa[0] = -1
				# Stop by injecting enough xacts.
				if checkExitCond():
					break
		futureChain = [xa for xa in futureChain if xa[0] != -1]
		print 'Future Events Chain: ', list(xa[0] for xa in futureChain)
		print 'Current Events Chain:', list(xa.index for xa in currentChain)
		for fac in facilities.values():
			if fac.busyxacts:
				fac.busyticks += 1
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
					if xact.curblk+1 >= len(toklines):
						pass #error: executive line index is out of bounds (probably missing '}}')
					print 'xact', xact.index, 'entering block', xact.curblk+1
					cmd = parser.parseBlock(toklines[xact.curblk+1])
					func = getattr(self, cmd[0])
					func(cmd[1])
				
					if xact.cond != 'canmove':
						if xact.cond == 'passagain':
							tempCurrentChain.append(xact)
							restart = True
						elif xact.cond == 'blocked':
							tempCurrentChain.append(xact)
							print 'xact', xact.index, 'was blocked'
						break
				# Stop by rejecting enough xacts.
				if checkExitCond():
					break
			currentChain = tempCurrentChain
			tempCurrentChain = []
		curticks += 1
		# Stop by modelling enough amount of time.
		if checkExitCond():
			break
			
	print_results()
	
def checkExitCond():
	global toklines
	global exitcond
	if parser.parseExitCond(toklines[exitcond]):
		return true
	return false	

def print_program():
	global toklines
	for line in toklines:
		for token in line:
			if token[0] in lexer.operators.values():
				print lexer.operators.keys()[lexer.operators.values().index(token[0])],
			elif token[0] == 'word' or token[0] == 'string' or \
			     token[0] == 'number' or token[0] == 'typedef' or \
			     token[0] == 'block':
				print token[1],
		print

def print_results():
	print '\n\n======== MODELLING INFORMATION ========'
	print '\nGenerated program:'
	print_program()
	print 'Modeling time: '+str(curticks)
	print '\n----Variables:----'
	for intt in ints.keys():
		print str(intt)+' = '+str(ints[intt].value)
	print '\n----Facilities:----'
	print 'Name\t   Mode\t\tBusyness\tCurrent xacts'
	print '- '*30
	for fac in facilities.values():
		l = []
		for xact in fac.busyxacts:
			l.append(xact.index)
		print fac.name+'\t   '+fac.mode+'\t{:.3f}\t\t{!s}'.format(fac.busyticks/float(curticks), l)
	print '\n----Queues:----'
	for qu in queues.values():
		print '{}\t{!s}\t{!s}'.format(qu.name, qu.enters, qu.curxacts)
	print '\n----Marks:----'
	for mark in marks.keys():
		print marks[mark].name+'\t'+str(marks[mark].block)
	print '\n----Future events chain:----'
	print 'Move time\tXact group\t\tXact ID\tXact curblock\tXact status'
	print '- '*35
	for xact in futureChain:
		print '{!s}\t\t{}\t\t{!s}\t{!s}\t\t{}'.format(xact[0], xact[1].group, 
				xact[1].index, xact[1].curblk, xact[1].cond)
	print '\n----Current events chain:----'
	print 'Xact group\t\tXact ID\tXact curblock\tXact status'
	print '- '*35
	for xact in currentChain:
		print xact.group+'\t\t'+str(xact.index)+'\t'	\
				+str(xact.curblk)+'\t\t'+xact.cond
