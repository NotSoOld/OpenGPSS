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
	def __init__(self, group, index, curblk, params={}):
		self.group = group
		self.index = index
		self.curblk = curblk
		self.params = params
		self.cond = 'injected'
	
def inject(injector):
	# Limit should be checked before calling this.
	global futureChain
	global curxact
	global curticks
	global injected
	xa = Xact(injector.group, injected, injector.block, injector.params)
	injected += 1
	if injector.limit != -1:
		injector.limit -= 1
	futime = curticks + injector.time + random.randint(-injector.tdelta, injector.tdelta)
	if injector.tdelay != 0:
		futime += injector.tdelay
		injector.tdelay = 0
	futureChain.append([futime, xa])

	
def queue_enter(qid):
	queues[qid].enters += 1
	queues[qid].curxacts += 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def queue_leave(qid):
	queues[qid].curxacts -= 1
	xact.curblk += 1
	xact.cond = 'canmove'
	
def fac_enter(fid):
	if facilities[fid].places > 0:
		facilities[fid].places -= 1
		facilities[fid].enters += 1
		xact.curblk += 1
		facilities[fid].busyxacts.append(xact)
		print 'added xact '+str(xact.index)+' to facility '+fid
		xact.cond = 'canmove'
	else:
		xact.cond = 'blocked'
	
def fac_leave(fid):
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

def move(args=[]):
	xact.curblk += 1
	xact.cond = 'canmove'		

	
###############################################################


def start_interpreter(filepath):
	progfile = open(filepath, 'r')
	allprogram = progfile.read()
	progfile.close()

	tokens = lexer.analyze(allprogram)
	
	global toklines
	global exitcond
	global curticks
	global xact
	global currentChain
	global futureChain
	global tempCurrentChain
	global facitilies
	global injectors
	
	toklines = parser.tocodelines(tokens)
	for line in toklines:
		print str(toklines.index(line)+1).zfill(2),
		print line
	print_program()
	ttt = raw_input()
	skip = False
	for line in toklines:
		if line == [['lexec', '']]:
			skip = True
		elif line == [['rexec', '']]:
			skip = False
			continue
		if skip == True:
			continue
		lineindex = toklines.index(line)+1
		if line[0][0] == 'typedef':
			defd = parser.parseDefinition(line)
			dic = globals()[defd[0]+'s']
			#dic = getattr(None, defd[0]+'s')
			if defd[1] in dic.keys():
				errors.print_error(22, lineindex, [defd[1], defd[0]])
			dic[defd[1]] = defd[2]
			if defd[0] == 'facilitie' and defd[2].isQueued:
				queues[defd[1]] = structs.Queue(defd[1])
		elif line[0][0] == 'block': 
			if line[0][1] == 'exitwhen':
				if exitcond != -1:
					errors.print_error(23, lineindex)
				exitcond = toklines.index(line)
			else:
				errors.print_warning(1, lineindex)
		else:
			errors.print_warning(1, lineindex)
				
	
	for line in toklines:
		if ['block', 'inject'] in line:
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
						errors.print_error(24, lineindex)
					print 'xact', xact.index, 'entering block', xact.curblk+1
					cmd = parser.parseBlock(toklines[xact.curblk+1])
					func = globals()[cmd[0]]
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
	if parser.parseExitCondition(toklines[exitcond]):
		return true
	return false	

def print_program():
	global toklines
	prog = ''
	for line in toklines:
		prog += str(toklines.index(line)+1).zfill(2)
		prog += '  '
		for token in line:
			t = ''
			if token[0] in lexer.operators.values():
				t = lexer.operators.keys()[lexer.operators.values().index(token[0])]
				if t in ',:':
					t += ' '
				elif t == '{':
					t = ' '+t
				elif t in '+,-,*,/,%,**,+=,-=,==,*=,/=,%=,**=,<,>,<=,>=,!=':
					t = ' '+t+' '
				prog += t
			elif token[0] == 'word' or token[0] == 'string' or \
			     token[0] == 'number' or token[0] == 'block':
				prog += token[1]
			elif token[0] == 'typedef':
				prog += token[1]+' '
		prog += '\n'
	print prog

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
