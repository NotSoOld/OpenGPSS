import sys
import random
import copy
import lexer
import parser
import structs
import errors

ints = {}
floats = {}
strs = {}
bools = {}
chains = {}
facilities = {}
queues = {}
marks = {}
chains = {}
injectors = {}
currentChain = []
tempCurrentChain = []
futureChain = []
xact = None
toklines = []
exitcond = -1
		
class Xact:
	def __init__(self, group, index, curblk, params={}):
		self.group = group
		self.index = index
		self.curblk = curblk
		self.params = params
		#if 'pr' not in self.params.keys():
		#	self.params['pr'] = 0
		self.cond = 'injected'
		self.eval_else = False
	
def inject(injector):
	# Limit should be checked before calling this.
	global futureChain
	global ints
	xa = Xact(injector.group, ints['injected'].value, injector.block, injector.params)
	ints['injected'].value += 1
	if injector.limit != -1:
		injector.limit -= 1
	random.seed()
	futime = ints['curticks'].value + injector.time + \
	         random.randint(-injector.tdelta, injector.tdelta)
	if injector.tdelay != 0:
		futime += injector.tdelay
		injector.tdelay = 0
	futureChain.append([futime, xa])

def queue_enter(qid):
	if qid not in queues.keys():
		errors.print_error(44, xact.curblk+1, [qid])
	if xact.index in queues[qid].queuedxacts:
		errors.print_error(39, xact.curblk+1)
	queues[qid].enters_q += 1
	queues[qid].curxacts += 1
	queues[qid].queuedxacts.append(xact.index)
	xact.curblk += 1
	xact.cond = 'canmove'
	
def queue_leave(qid):
	if qid not in queues.keys():
		errors.print_error(44, xact.curblk+1, [qid])
	if xact.index not in queues[qid].queuedxacts:
		errors.print_error(40, xact.curblk+1)
	queues[qid].curxacts -= 1
	queues[qid].queuedxacts.remove(xact.index)
	xact.curblk += 1
	xact.cond = 'canmove'
	
def fac_enter(fid, v=1):
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	if facilities[fid].isQueued:
		if xact.index not in queues[fid].queuedxacts:
			queue_enter(fid)
			xact.curblk -= 1
		
	if facilities[fid].curplaces - v >= 0:
		facilities[fid].curplaces -= v
		facilities[fid].enters_f += 1
		if xact.index in facilities[fid].busyxacts:
			errors.print_error(41, xact.curblk+1)
		facilities[fid].busyxacts[xact.index] = [v, 'entered']
		#print 'added xact '+str(xact.index)+' to facility '+fid
		
		if facilities[fid].isQueued:
			queue_leave(fid)
			xact.curblk -= 1
		xact.curblk += 1
		xact.cond = 'canmove'
	else:
		xact.cond = 'blocked'
	
def fac_leave(fid):
	if xact.index not in facilities[fid].busyxacts:
		errors.print_error(42, xact.curblk+1)
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	leaving = facilities[fid].busyxacts[xact.index]
	facilities[fid].curplaces += leaving[0]
	del facilities[fid].busyxacts[xact.index]
	review_cec()
	
def fac_irrupt(fid, vol, eject=False, mark='', elapsedto=[]):
	# (fac, 1) === (fac, 1, False)
	# (fac, 1, True) <-- eject xact and call move() for it
	# (fac, 1, True, mark1) <-- eject to mark1
	# (fac, 1, True, mark1, xact.p1) or
	# (fac, 1, True, '', xact.p1) <-- in addition, save elapsed time to xact.p1
	# (fac, 1, False) <-- flush to irrupt chain and save elapsed time
	# (fac, 1, False, ...) <-- prohibited!
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	if xact.index in facilities[fid].busyxacts:
		errors.print_error(47, xact.curblk+1)
	if mark != '':
		if mark not in marks.keys():
			errors.print_error(29, xact.curblk+1, [mark])
		if marks[mark].block == -1:
			errors.print_error(30, xact.curblk+1, [mark])
	
	if facilities.maxplaces < vol:
		move()
		return
	if facilities[fid].curplaces == facilities[fid].maxplaces:
		fac_enter(fid, vol)
		return
		
	while True:
		if facilities[fid].curplaces == vol:
			break
			
		# Take xact info from busy xacts.
		ir_vol = facilities[fid].busyxacts[facilities[fid].busyxacts.keys()[-1]]
		ir_index = facilities[fid].busyxacts.keys()[-1]
		# Free facility from this xact.
		del facilities[fid].busyxacts[ir_index]
		facilities[fid].curplaces += ir_vol[0]
		# Find this xact in one of system chains and pull it to CEC/irrput chain.
		found = False
		for i in range(len(currentChain)):
			if currentChain[i].index == ir_index:
				found = True
				break
		if found:
			if eject:
				xa = copy.deepcopy(currentChain[i])
				xa.cond = 'canmove'
				if mark == '':
					xa.curblk = xact.curblk + 1
				else:
					xa.curblk = marks[mark].block - 1
				# additionally parse assignment here (elapsed time = 0)
				if elapsedto != []:
					elapsedto += [['eq', ''], ['number', 0], ['eocl', '']]
					# We need 'xa' for assignment:
					oldxact = copy.deepcopy(xact)
					xact = xa
					parser.parseAssignment(elapsedto)
					xact = oldxact
				currentChain.append(xa)
			else:
				facilities[fid].irruptch.append([copy.deepcopy(currentChain[i]), 
				                               0, ir_vol])
			del currentChain[i]
			continue
			
		found = False
		for i in range(len(futureChain)):
			if futureChain[i][1].index == ir_index:
				found = True
				break
		if found:
			if eject:
				xa = copy.deepcopy(futureChain[i][1])
				xa.cond = 'canmove'
				if mark == '':
					xa.curblk = xact.curblk + 1
				else:
					xa.curblk = marks[mark].block - 1
				# additionally parse assignment here 
				# (elapsed time = futureChain[i][0] - ints['curticks'])
				if elapsedto != []:
					elapsed = futureChain[i][0] - ints['curticks']
					elapsedto += [['eq', ''], ['number', elapsed], ['eocl', '']]
					# We need 'xa' for assignment:
					oldxact = copy.deepcopy(xact)
					xact = xa
					parser.parseAssignment(elapsedto)
					xact = oldxact
				currentChain.append(xa)
			else:
				facilities[fid].irruptch.append(
				     [copy.deepcopy(futureChain[i][1]),
				     futureChain[i][0] - ints['curticks'], ir_vol])
			del futureChain[i]
			continue
			
		for ch in chains.keys():
			found = False
			for i in range(chains[ch].length):
				if chains[ch].xacts[i].index == ir_index:
					found = True
					break
			if found:
				if eject:
					xa = copy.deepcopy(chains[ch].xacts[i])
					xa.cond = 'canmove'
					if mark == '':
						xa.curblk = xact.curblk + 1
					else:
						xa.curblk = marks[mark].block - 1
					# additionally parse assignment here 
					# (elapsed time = 0)
					if elapsedto != []:
						elapsedto += [['eq', ''], ['number', 0], ['eocl', '']]
						# We need 'xa' for assignment:
						oldxact = copy.deepcopy(xact)
						xact = xa
						parser.parseAssignment(elapsedto)
						xact = oldxact
					currentChain.append(xa)
				else:
					facilities[fid].irruptch.append(
					          [copy.deepcopy(chains[ch].xacts[i]), 0, ir_vol])
				del chains[ch].xacts[i]
				chains[ch].length = len(chains[ch].xacts)
				break
	# Add irrupting xact to facility (will always succeed).
	fac_enter(fid, vol)
		
def fac_goaway(fid):
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	if xact.index not in facilities[fid].busyxacts:
		errors.print_error(48, xact.curblk+1)
	
	# Delete this xact from facility.
	go = facilities[fid].busyxacts[xact.index]
	facilities[fid].curplaces += go[0]
	del facilities[fid].busyxacts[xact.index]
	review_cec()
	# Move xacts to freed places from irrupt chain.
	for i in range(len(facilities[fid].irruptch)):
		xainfo = facilities[fid].irruptch[i]
		if facilities[fid].curplaces < xainfo[2]:
			continue
		if xainfo[1] == 0:
			currentChain.append(copy.deepcopy(xainfo[0]))
		else:
			futureChain.append([xainfo[1], copy.deepcopy(xainfo[0])])
		facilities[fid].busyxacts[xainfo[0].index] = [xainfo[2], 'entered']
		#print 'added xact '+str(xainfo[0].index)+' back to facility '+fid
		facilities[fid].curplaces += xainfo[2]
		facilities[fid].irruptch[i] = []
	facilities[fid].irruptch = [el for el in facilities[fid].irruptch if el != []]
	
def wait(time, tdelta=0):
	global futureChain
	global ints
	random.seed()
	futime = ints['curticks'].value + time + random.randint(-tdelta, tdelta)
	xact.curblk += 1
	xact.cond = 'waiting'
	print 'exit time =', futime
	futureChain.append([futime, xact])
	
def reject(decr):
	global ints
	ints['rejected'].value += decr
	xact.curblk += 1
	for fac in facilities.keys():
		if xact.index in facilities[fac].busyxacts:
			fac_leave(fac)
			xact.curblk -= 1
	for qu in queues.keys():
		if xact.index in queues[qu].queuedxacts:
			queue_leave(qu)
			xact.curblk -= 1
	xact.cond = 'rejected'
	
def chain_enter(chid):
	chains[chid].xacts.append(xact)
	chains[chid].length = len(chains[chid].xacts)
	xact.cond = 'chained'
	
def chain_leave(chid, cnt, toblk=''):
	if toblk != '':
		if toblk not in marks.keys():
			errors.print_error(29, xact.curblk+1, [toblk])
		if marks[toblk].block == -1:
			errors.print_error(30, xact.curblk+1, [toblk])
	move()
	for i in range(cnt):
		if len(chains[chid].xacts) == 0:
			continue
		xa = chains[chid].xacts.pop()
		chains[chid].length = len(chains[chid].xacts)
		xa.cond = 'canmove'
		if toblk != '':
			xa.curblk = marks[toblk].block - 1
		else:
			xa.curblk = xact.curblk
		tempCurrentChain.append(xa)
	
def chain_purge(chid, toblk=''):
	chain_leave(chid, len(chains[chid].xacts), toblk)
	
#def chain_leaveif(chid, cond, cnt, toblk=''):
#	pass
	
def if_block(cond):
	if cond:
		xact.curblk += 1
		move()
		xact.eval_else = False
		return
	
	depth = 0
	global toklines
	for i in range(xact.curblk+2, len(toklines)):
		if toklines[i][0][0] == 'lbrace':
			depth += 1
		elif toklines[i][0][0] == 'rbrace':
			depth -= 1
		if depth == 0:
			break
	if depth != 0:
		errors.print_error(36, i)
	xact.curblk = i
	xact.cond = 'canmove'
	xact.eval_else = True
	
def else_if_block(cond):
	if xact.eval_else:
		if_block(cond)
	else:
		if_block(False)
		xact.eval_else = False
	
def else_block(args=[]):
	if xact.eval_else:
		if_block(True)
	else:
		if_block(False)
		xact.eval_else = False
	
def try_block(cond):
	if cond:
		xact.curblk += 1
		move()
	else:
		xact.cond = 'blocked'
		
def while_block(cond):
	if cond:
		xact.curblk += 1
		move()
		return
		
	depth = 0
	global toklines
	for i in range(xact.curblk+2, len(toklines)):
		if toklines[i][0][0] == 'lbrace':
			depth += 1
		elif toklines[i][0][0] == 'rbrace':
			depth -= 1
		if depth == 0:
			break
	if depth != 0:
		errors.print_error(37, i)
	xact.curblk = i
	xact.cond = 'canmove'

def move(args=[]):
	xact.curblk += 1
	xact.cond = 'canmove'
	
def review_cec(args=[]):
	move()
	xact.cond = 'passagain'
	
def transport(block):
	transport_if(block, True)

def transport_prob(block, prob, addblock=''):
	random.seed()
	transport_if(block, random.random() < prob, addblock)
	
def transport_if(block, cond, addblock=''):
	xact.cond = 'canmove'
	if block not in marks.keys():
		errors.print_error(29, xact.curblk+1, [block])
	if marks[block].block == -1:
		errors.print_error(30, xact.curblk+1, [block])
		
	if cond:
		xact.curblk = marks[block].block-1
	else:
		if addblock == '':
			xact.curblk += 1
		else:
			if addblock not in marks.keys():
				errors.print_error(29, xact.curblk+1, [addblock])
			if marks[block].block == -1:
				errors.print_error(30, xact.curblk+1, [addblock])
			xact.curblk = marks[addblock].block-1

def output(outstr):
	print '(T={!s}'.format(ints['curticks'].value).ljust(9) + \
	       'L={!s}'.format(xact.curblk+1).ljust(8) + \
	      'X={!s})'.format(xact.index).ljust(8) + \
	      '{!s}'.format(outstr.decode('string_escape'))
	move()
	
def xact_report(args=[]):
	move()
	s = '\n'+'-'*20
	s += '\nXact {!s} (group "{!s}") in line {!s} at beat {!s}:\n'.format(
	     xact.index, xact.group, xact.curblk, ints['curticks'].value)
	s += 'Priority: {!s}\n'.format(xact.params['pr'])
	s1 = ''
	for par in xact.params:
		if par != 'pr':
			s1 += '{!s} = {!s}\n'.format(par, xact.params[par])
	s += 'Parameters:\n'+s1
	s += '-'*20
	print s
	print
	
def copy_block(cnt, toblk=''):
	global ints
	if toblk != '':
		if toblk not in marks.keys():
			errors.print_error(29, xact.curblk+1, [toblk])
		if marks[toblk].block == -1:
			errors.print_error(30, xact.curblk+1, [toblk])
	move()
	for i in range(cnt):
		xa = copy.deepcopy(xact)
		if toblk != '':
			xa.curblk = marks[toblk].block - 1
		else:
			xa.curblk += 1
		xa.cond = 'canmove'
		xa.index = ints['injected'].value
		ints['injected'].value += 1
		tempCurrentChain.append(xa)
	
def interrupt(args=[]):
	move()
	xact.cond = 'interrupt'
	
def flush_cec(args=[]):
	move()
	for fac in facilities.keys():
		if xact.index in facilities[fac].busyxacts:
			fac_leave(fac)
			xact.curblk -= 1
	for qu in queues.keys():
		if xact.index in queues[qu].queuedxacts:
			queue_leave(qu)
			xact.curblk -= 1
	xact.cond = 'flush'
	
def pause_by_user(s=''):
	print 'Paused in line {!s}'.format(xact.curblk+1),
	if s:
		print ': {!s}'.format(s)
	print 'Press any key to continue.'
	trash = raw_input()
	move()
	
###############################################################


def start_interpreter(filepath):
	progfile = open(filepath, 'r')
	allprogram = progfile.read()
	progfile.close()

	tokens = lexer.analyze(allprogram)
	
	global toklines
	global exitcond
	global xact
	global currentChain
	global futureChain
	global tempCurrentChain
	global facitilies
	global injectors
	global ints
	
	toklines = parser.tocodelines(tokens)
	toklines = parser.convertBlocks(toklines)
	for line in toklines:
		print str(line[-1][0]).zfill(2),
		print line
	print
	print_program()
	
	addDefaultVars()
	skip = False
	for line in toklines[1:]:
		if line[0] == ['lexec', '']:
			skip = True
		elif line[0] == ['rexec', '']:
			skip = False
			continue
		if skip == True:
			continue
		lineindex = line[-1][0]
		if line[0][0] == 'typedef':
			defd = parser.parseDefinition(line)
			#print defd
			dic = globals()[defd[0]+'s']
			if defd[1] in dic.keys():
				errors.print_error(22, lineindex, [defd[1], defd[0]])
			dic[defd[1]] = defd[2]
			if defd[0] == 'facilitie' and defd[2].isQueued:
				queues[defd[1]] = structs.Queue(defd[1])
		elif line[0][0] == 'block': 
			if line[0][1] == 'exitwhen':
				if exitcond != -1:
					errors.print_error(23, lineindex)
				exitcond = line[-1][0]
			else:
				errors.print_warning(1, lineindex)
		else:
			errors.print_warning(1, lineindex)
	
	ttt = raw_input('Read the info above, it may contain some warnings. When '\
					'ready, press any key')			
	
	for line in toklines:
		if ['block', 'inject'] in line:
			newinj = parser.parseInjector(line)
			injectors[newinj.group] = newinj
			inject(newinj)
			
	while True:
		tempCurrentChain = []
		print 'timestep =', ints['curticks'].value
		ttt = raw_input()
		
		# Statistics gathering.
		for fac in facilities.values():
			if fac.busyxacts:
				fac.busyticks += len(fac.busyxacts)/float(fac.maxplaces)
		
		for xa in futureChain:
			if xa[0] == ints['curticks'].value:
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
		currentChain = sorted(currentChain, key=lambda xa: xa.params['pr'])
		currentChain.reverse()
		print 'Future Events Chain: ', list(xa[0] for xa in futureChain)
		
		restart = True
		interrupt = False
		flush = False
		while restart:
			currentChain = sorted(currentChain, key=lambda xa: xa.params['pr'])
			currentChain.reverse()
			print 'Current Events Chain:', list(xa.index for xa in currentChain)
			restart = False
			for cxact in currentChain:
				xact = copy.deepcopy(cxact)
				if restart or interrupt:
					tempCurrentChain.append(xact)
					continue
				while True:
					if xact.curblk+1 >= len(toklines):
						errors.print_error(24, lineindex)
					print 'xact', xact.index, 'entering block', xact.curblk+1
					cmd = parser.parseBlock(toklines[xact.curblk+1])
					#print cmd
					#ttt = raw_input()
					func = globals()[cmd[0]]
					func(*cmd[1])
				
					if xact.cond != 'canmove':
						if xact.cond == 'rejected':
							restart = True
						if xact.cond == 'passagain':
							tempCurrentChain.append(xact)
							restart = True
						elif xact.cond == 'blocked':
							tempCurrentChain.append(xact)
							print 'xact', xact.index, 'was blocked'
						elif xact.cond == 'interrupt':
							tempCurrentChain.append(xact)
							interrupt = True
						elif xact.cond == 'flush':
							flush = True
						break
				if flush:
					currentChain = []
					tempCurrentChain = []
					break
				# Stop by rejecting enough xacts.
				if checkExitCond():
					break
			currentChain = tempCurrentChain
			tempCurrentChain = []
		ints['curticks'].value += 1
		# Stop by modelling enough amount of time.
		if checkExitCond():
			break
			
	print_results()
	
def checkExitCond():
	global toklines
	global exitcond
	if parser.parseExitCondition(toklines[exitcond]):
		return True
	return False	

def addDefaultVars():
	global ints
	ints['injected'] = structs.IntVar('injected', 0)
	ints['rejected'] = structs.IntVar('rejected', 0)
	ints['curticks'] = structs.IntVar('curticks', 0)

def print_program():
	global toklines
	prog = ''
	for line in toklines[1:]:
		prog += str(line[-1][0]).zfill(2)
		prog += '  '
		for token in line:
			t = ''
			if token[0] in lexer.operators.values():
				t = lexer.operators.keys()[lexer.operators.values()
										   .index(token[0])]
				if t in ',:' or t == '->':
					t += ' '
				elif t == '{':
					t = ' '+t
				elif t in '+,-,*,/,%,**,+=,-=,==,*=,/=,%=,**=,<,>,<=,>=,!=':
					t = ' '+t+' '
				prog += t
			elif token[0] == 'word' or \
				 token[0] == 'number' or token[0] == 'block' or \
				 token[0] == 'builtin':
				prog += token[1]
			elif token[0] == 'string':
				prog += '"'+token[1]+'"'
			elif token[0] == 'typedef':
				prog += token[1]+' '
		prog += '\n'
	print prog

def print_results():
	print '\n\n\n\n======== MODELLING INFORMATION ========'
	
	print '\n\n----Generated program:----'
	print_program()
	print '\nModeling time: '+str(ints['curticks'].value)+' beats'
	
	if ints.keys():
		print '\n\n----Integer variables:----'
		for intt in ints.keys():
			print str(intt)+' = '+str(ints[intt].value)
	
	if floats.keys():
		print '\n\n----Float variables:----'
		for floatt in floats.keys():
			print str(floatt)+' = '+str(floats[floatt].value)
			
	if strs.keys():
		print '\n\n----String variables:----'
		for s in strs.keys():
			print s+' = '+repr(strs[s].value)
	
	print '\n\n----Facilities:----'
	if not facilities.keys():
		print '<<NO FACILITIES>>'
	else:
		print 'Name   \tMax xacts\tAuto queued\tEnters\t\t'\
			  'Busyness\tCurrent xacts'
		print '- '*40
		for fac in facilities.values():
			print '{!s}   \t{!s}\t\t{!s}\t\t{!s}\t\t{:.3f}\t\t{!s}'.format(
				  fac.name, fac.maxplaces, fac.isQueued, fac.enters_f,
				  fac.busyticks/float(ints['curticks'].value), 
				  fac.busyxacts)

	print '\n\n----Queues:----'
	if not queues.keys():
		print '<<NO QUEUES>>'
	else:
		print 'Name   \t\tEnters\t\tCurrent xacts'
		print '- '*40
		for qu in queues.values():
			print '{}   \t\t{!s}\t\t{!s}'.format(
				  qu.name, qu.enters_q, qu.curxacts)
				  
	print '\n\n----User chains:----'
	if not queues.keys():
		print '<<NO USER CHAINS>>'
	else:
		print 'Name   \t\tLength\t\tCurrent xacts'
		print '- '*40
		for ch in chains.values():
			print '{}   \t\t{!s}\t\t{!s}'.format(
				  ch.name, ch.length, [xa.index for xa in ch.xacts])
	
	global marks
	marks = {k:v for k,v in marks.items() if not k.startswith('&')}
	if marks.keys():
		print '\n\n----Marks:----'
		print 'Name   \tCorresponding line'
		print '- '*40
		for mark in marks.keys():
			print '{}   \t{!s}'.format(marks[mark].name, marks[mark].block)
		
	print '\n\n----Future events chain:----'
	if not futureChain:
		print '<<EMPTY>>'
	else:
		print 'Move time\tXact group\tXact ID   \tXact curblock\tXact status'
		print '- '*40
		for xact in futureChain:
			print '{!s}\t\t{}\t\t{!s}   \t\t{!s}\t\t{}'.format(
				  xact[0], xact[1].group, 
				  xact[1].index, xact[1].curblk, xact[1].cond)
				
	print '\n\n----Current events chain:----'
	if not currentChain+tempCurrentChain:
		print '<<EMPTY>>'
	else:
		print 'Xact group\tXact ID   \tXact curblock\tXact status'
		print '- '*40
		for xact in currentChain+tempCurrentChain:
			print '{}\t\t{!s}   \t\t{!s}\t\t{}'.format(
				  xact.group, xact.index, xact.curblk, xact.cond)
				  
	print
	print
