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
hists = {}
currentChain = []
tempCurrentChain = []
futureChain = []
xact = None
chxact = None
toklines = []
exitcond = -1
		
class Xact:
	def __init__(self, group, index, curblk, params={}):
		self.group = group
		self.index = index
		self.curblk = curblk
		self.params = params
		self.cond = 'injected'
		self.eval_else = False
	
def inject(injector):
	# Limit should be checked before calling this.
	global futureChain
	global ints
	global toklines
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
	toklines[xa.curblk][-1][2] += 1

def queue_enter(qid):
	global toklines
	if qid not in queues.keys():
		errors.print_error(44, xact.curblk+1, [qid])
	if xact.index in queues[qid].queuedxacts:
		errors.print_error(39, xact.curblk+1)
	queues[qid].enters_q += 1
	queues[qid].curxacts += 1
	queues[qid].queuedxacts.append(xact.index)
	xact.curblk += 1
	xact.cond = 'canmove'
	toklines[xact.curblk][-1][2] += 1
	
def queue_leave(qid):
	global toklines
	if qid not in queues.keys():
		errors.print_error(44, xact.curblk+1, [qid])
	if xact.index not in queues[qid].queuedxacts:
		errors.print_error(40, xact.curblk+1)
	queues[qid].curxacts -= 1
	queues[qid].queuedxacts.remove(xact.index)
	xact.curblk += 1
	xact.cond = 'canmove'
	toklines[xact.curblk][-1][2] += 1
	
def fac_enter(fid, v=1):
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	if facilities[fid].isQueued:
		if xact.index not in queues[fid].queuedxacts:
			queue_enter(fid)
			toklines[xact.curblk][-1][2] -= 1
			xact.curblk -= 1
		
	if facilities[fid].curplaces - v >= 0:
		facilities[fid].curplaces -= v
		facilities[fid].enters_f += 1
		if xact.index in facilities[fid].busyxacts:
			errors.print_error(41, xact.curblk+1)
		facilities[fid].busyxacts[xact.index] = [v, ints['curticks'].value]
		#print 'added xact '+str(xact.index)+' to facility '+fid
		
		if facilities[fid].isQueued:
			queue_leave(fid)
			toklines[xact.curblk][-1][2] -= 1
			xact.curblk -= 1
		xact.curblk += 1
		xact.cond = 'canmove'
		toklines[xact.curblk][-1][2] += 1
	else:
		xact.cond = 'blocked'
	
def fac_leave(fid):
	if xact.index not in facilities[fid].busyxacts:
		errors.print_error(42, xact.curblk+1)
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	leaving = facilities[fid].busyxacts[xact.index]
	facilities[fid].curplaces += leaving[0]
	facilities[fid].processedxactsticks += ints['curticks'].value - leaving[1]
	del facilities[fid].busyxacts[xact.index]
	review_cec()
	
def fac_irrupt(fid, vol=1, eject=False, mark='', elapsedto=[]):
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
	
	if facilities[fid].maxplaces < vol:
		move()
		return
	if facilities[fid].curplaces == facilities[fid].maxplaces:
		fac_enter(fid, vol)
		return
		
	while True:
		if facilities[fid].curplaces == vol:
			break
			
		# Take xact info from busy xacts.
		ir_index = facilities[fid].busyxacts.keys()[-1]
		ir_vol = facilities[fid].busyxacts[ir_index]
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
					# (pos and tokline are corrected automatically
					# in parseAssignment)
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
					elapsed = futureChain[i][0] - ints['curticks'].value
					elapsedto += [['eq', ''], ['number', elapsed], ['eocl', '']]
					# We need 'xa' for assignment:
					# (pos and tokline are corrected automatically
					# in parseAssignment)
					oldxact = copy.deepcopy(xact)
					xact = xa
					parser.parseAssignment(elapsedto)
					xact = oldxact
				currentChain.append(xa)
			else:
				facilities[fid].irruptch.append(
				     [copy.deepcopy(futureChain[i][1]),
				     futureChain[i][0] - ints['curticks'].value, ir_vol])
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
						# (pos and tokline are corrected automatically
						# in parseAssignment)
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
	# Because this xact could skip fac_irrupt() block because it's too "fat"
	# to irrupt that facility:
	if xact.index not in facilities[fid].busyxacts:
		move()
		return
		
	# Delete this xact from facility.
	# go: [vol, enter time]
	go = facilities[fid].busyxacts[xact.index]
	facilities[fid].curplaces += go[0]
	del facilities[fid].busyxacts[xact.index]
	review_cec()
	# Move xacts to freed places from irrupt chain.
	for i in range(len(facilities[fid].irruptch)):
		# xainfo: [xact, elapsed time, [xact vol, enter time]]
		xainfo = facilities[fid].irruptch[i]
		if facilities[fid].curplaces < xainfo[2][0]:
			continue
		if xainfo[1] == 0:
			currentChain.append(copy.deepcopy(xainfo[0]))
		else:
			futureChain.append([xainfo[1], copy.deepcopy(xainfo[0])])
		facilities[fid].busyxacts[xainfo[0].index] = xainfo[2]
		#print 'added xact '+str(xainfo[0].index)+' back to facility '+fid
		facilities[fid].curplaces += xainfo[2][0]
		facilities[fid].irruptch[i] = []
	facilities[fid].irruptch = [el for el in facilities[fid].irruptch if el != []]
	
def wait(time, tdelta=0):
	global futureChain
	global ints
	global toklines
	random.seed()
	futime = ints['curticks'].value + time + random.randint(-tdelta, tdelta)
	xact.curblk += 1
	xact.cond = 'waiting'
	toklines[xact.curblk][-1][2] += 1
	print 'exit time =', futime
	futureChain.append([futime, xact])
	
def reject(decr):
	global ints
	global toklines
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
	toklines[xact.curblk][-1][2] += 1
	
def chain_enter(chid):
	global toklines
	chains[chid].xacts.append(xact)
	chains[chid].length = len(chains[chid].xacts)
	xact.cond = 'chained'
	toklines[xact.curblk+1][-1][2] += 1
	
def chain_leave(chid, cnt, toblk=''):
	if toblk != '':
		if toblk not in marks.keys():
			errors.print_error(29, xact.curblk+1, [toblk])
		if marks[toblk].block == -1:
			errors.print_error(30, xact.curblk+1, [toblk])
	move()
	for i in range(cnt):
		if len(chains[chid].xacts) == 0:
			break
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
	
def chain_pick(chid, cond, cnt, toblk=''):
	# chain_pick(buf, chxact.p1 == 10, 5) => will pick all xacts from buf 
	#                                        according to condition (5 or less)
	if toblk != '':
		if toblk not in marks.keys():
			errors.print_error(29, xact.curblk+1, [toblk])
		if marks[toblk].block == -1:
			errors.print_error(30, xact.curblk+1, [toblk])
	move()
	global chxact
	while True:
		if len(chains[chid].xacts) == 0:
			break
		for temp_chxa in chains[chid].xacts:
			chxact = copy.deepcopy(temp_chxa)
			parser.pos = 0
			parser.tokline = cond
			if parser.parseExpression():
				cnt -= 1
				xa = copy.deepcopy(chxact)
				chains[chid].xacts.remove(temp_chxa)
				chains[chid].length = len(chains[chid].xacts)
				xa.cond = 'canmove'
				if toblk != '':
					xa.curblk = marks[toblk].block - 1
				else:
					xa.curblk = xact.curblk
				tempCurrentChain.append(xa)
				break
		if cnt == 0:
			break
	chxact = None		
			
def chain_find(chid, index_expr, cnt, toblk):
	# chain_find(buf, find(buf.xacts.pr < 10), 5) => will evaluate condition 5 times
	if toblk != '':
		if toblk not in marks.keys():
			errors.print_error(29, xact.curblk+1, [toblk])
		if marks[toblk].block == -1:
			errors.print_error(30, xact.curblk+1, [toblk])
	move()
	while True:
		if len(chains[chid].xacts) == 0:
			break
		index = -1
		if type(index_expr) is int:
			index = index_expr
		else:
			parser.pos = 0
			parser.tokline = index_expr
			index = parser.parseExpression()
		for chxa in chains[chid].xacts:
			if chxa.index == index:
				cnt -= 1
				xa = copy.deepcopy(chxa)
				chains[chid].xacts.remove(chxa)
				chains[chid].length = len(chains[chid].xacts)
				xa.cond = 'canmove'
				if toblk != '':
					xa.curblk = marks[toblk].block - 1
				else:
					xa.curblk = xact.curblk
				tempCurrentChain.append(xa)
				break
		if cnt == 0:
			break
	
def if_block(cond):
	global toklines
	if cond:
		xact.curblk += 1
		toklines[xact.curblk][-1][2] += 1
		move()
		xact.eval_else = False
		return
	
	depth = 0
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
	toklines[xact.curblk][-1][2] += 1
	
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
	
def wait_until(cond):
	if cond:
		move()
	else:
		xact.cond = 'blocked'
		
def while_block(cond):
	global toklines
	if cond:
		xact.curblk += 1
		toklines[xact.curblk][-1][2] += 1
		move()
		return
		
	depth = 0
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
	toklines[xact.curblk][-1][2] += 1

def move(args=[]):
	global toklines
	xact.curblk += 1
	xact.cond = 'canmove'
	toklines[xact.curblk][-1][2] += 1
	
def review_cec(args=[]):
	move()
	xact.cond = 'passagain'
	
def transport(block):
	transport_if(block, True)

def transport_prob(block, prob, addblock=''):
	random.seed()
	transport_if(block, random.random() < prob, addblock)
	
def transport_if(block, cond, addblock=''):
	global toklines
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
	toklines[xact.curblk][-1][2] += 1

def output(outstr):
	outstr = str(outstr)
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
	s += 'Priority: {!s}\n'.format(xact.params['priority'])
	s1 = ''
	for par in xact.params:
		if par != 'priority':
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
	
def hist_add(hist):
	if hist not in hists.keys():
		errors.print_error(53, xact.curblk+1, [hist])
		
	parser.tokline = hists[hist].param
	parser.pos = 0
	val = parser.parseExpression()
	hists[hist].add(val)
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
		print '\ntimestep =', ints['curticks'].value
		#ttt = raw_input()
		
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
		futureChain = [xa for xa in futureChain if xa[0] != -1]
		print 'Future Events Chain: ', list(xa[0] for xa in futureChain)
		
		restart = True
		interrupt = False
		flush = False
		while restart:
			currentChain = sorted(currentChain, key=lambda xa: xa.params['priority'])
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
					
					# Let's try:
					#if xact.cond != 'blocked':
					#	toklines[xact.curblk][-1][2] += 1
				
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
			currentChain = tempCurrentChain
			tempCurrentChain = []
		ints['curticks'].value += 1
			
		# Statistics gathering.
		for fac in facilities.values():
			if fac.busyxacts:
				fac.busyticks += len(fac.busyxacts)/float(fac.maxplaces)
				
		# Stop modelling.
		if checkExitCond():
			break
	
	count_xacts_on_blocks()
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

def count_xacts_on_blocks():
	# Only xacts from CEC and FEC are counted.
	for xa in currentChain:
		toklines[xa.curblk][-1][1] += 1
	for xa in futureChain:
		toklines[xa[1].curblk][-1][1] += 1

def print_program():
	global toklines
	prog = ''
	max0 = 0
	max1 = 0
	max2 = 0
	for line in toklines[1:]:
		if len(str(line[-1][0])) > max0:
			max0 = len(str(line[-1][0]))
		if len(str(line[-1][1])) > max1:
			max1 = len(str(line[-1][1]))
		if len(str(line[-1][2])) > max2:
			max2 = len(str(line[-1][2]))
		
	for line in toklines[1:]:
		prog += str(line[-1][0]).zfill(max0)
		prog += '  '
		if line[-1][1] != 0:
			prog += str(line[-1][1]).zfill(max1)
		else:
			prog += ' '*max1
		prog += '  '
		if line[-1][2] != 0:
			prog += str(line[-1][2]).zfill(max2)
		else:
			prog += ' '*max2
		prog += '  '
		prevtoken = []
		for token in line:
			t = ''
			if token[0] in lexer.operators.values():
				t = lexer.operators.keys()[lexer.operators.values()
										   .index(token[0])]
				if t in ',:':
					t += ' '
				elif t == '{':
					t = ' '+t
				elif t == '>' and prevtoken[0] == 'transport':
					pass
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
			prevtoken = token
		prog += '\n'
	print prog

def print_results():
	print '\n\n\n\n======== MODELLING INFORMATION ========'
	
	print '\n\n---- Generated program: ----\n' \
	      '(line index, current xacts, total executions, line of code)\n'
	print_program()
	print '\nModeling time: '+str(ints['curticks'].value)+' beats'
	
	if ints.keys():
		print '\n\n---- Integer variables: ----'
		for intt in ints.keys():
			print str(intt)+' = '+str(ints[intt].value)
	
	if floats.keys():
		print '\n\n---- Float variables: ----'
		for floatt in floats.keys():
			print str(floatt)+' = '+str(floats[floatt].value)
			
	if strs.keys():
		print '\n\n---- String variables: ----'
		for s in strs.keys():
			print s+' = '+repr(strs[s].value)
	
	print '\n\n---- Facilities: ----'
	if not facilities.keys():
		print '<<NO FACILITIES>>'
	else:
		lname = 0
		for fac in facilities.values():
			if len(fac.name) > lname:
				lname = len(fac.name)
		print ''.ljust(lname+5+13+16+11+13) + \
		      'Average'.ljust(19) + \
		      'Current xacts'
		print 'Name'.ljust(lname+5) + \
		      'Max xacts'.ljust(13) + \
		      'Auto queued'.ljust(16) + \
		      'Enters'.ljust(11) + \
		      'Busyness'.ljust(13) + \
		      'processing time'.ljust(19) + \
		      '(index: [vol, enter time])'
		print '- '*45
		for fac in facilities.values():
			print str(fac.name).ljust(lname+5) + \
			      str(fac.maxplaces).ljust(13) + \
			      str(fac.isQueued).ljust(16) + \
			      str(fac.enters_f).ljust(11) + \
			      ('{:.3f}'.format(fac.busyticks/float(ints['curticks']
			      .value)).ljust(13)) + \
			      ('{:.2f}'.format(fac.processedxactsticks/float(
			      fac.enters_f - (fac.maxplaces - fac.curplaces)))).ljust(19) + \
			      str(fac.busyxacts)

	print '\n\n---- Queues: ----'
	if not queues.keys():
		print '<<NO QUEUES>>'
	else:
		lname = 0
		for qu in queues.values():
			if len(qu.name) > lname:
				lname = len(qu.name)
		print 'Name'.ljust(lname+5) + \
		      'Enters'.ljust(11) + \
		      'Current length'.ljust(19) + \
		      'Current xacts (indexes)'
		print '- '*40
		for qu in queues.values():
			print str(qu.name).ljust(lname+5) + \
			      str(qu.enters_q).ljust(11) + \
			      str(qu.curxacts).ljust(19) + \
			      str(qu.queuedxacts)
				  
	print '\n\n---- User chains: ----'
	if not chains.keys():
		print '<<NO USER CHAINS>>'
	else:
		lname = 0
		for ch in chains.values():
			if len(ch.name) > lname:
				lname = len(ch.name)
		print 'Name'.ljust(lname+5) + \
		      'Current length'.ljust(19) + \
		      'Current xacts (indexes)'
		print '- '*40
		for ch in chains.values():
			print str(ch.name).ljust(lname+5) + \
			      str(ch.length).ljust(19) + \
			      str([xa.index for xa in ch.xacts])
	
	global marks
	marks = {k:v for k,v in marks.items() if not k.startswith('&')}
	if marks.keys():
		print '\n\n---- Marks: ----'
		lname = 0
		for mark in marks.keys():
			if len(mark) > lname:
				lname = len(mark)
		print 'Name'.ljust(lname+5) + \
		      'Corresponding line'
		print '- '*40
		for mark in marks.keys():
			print str(marks[mark].name).ljust(lname+5) + \
			      str(marks[mark].block)
	
	print '\n\n---- Histograms: ----\n'
	if not hists.keys():
		print '<<NO HISTOGRAMS>>'
	else:
		for hist in hists.values():
			totalcnt = 0
			for i in hist.intervals:
				totalcnt += i
			lname = len(hist.name)+4
			par = ''
			for t in hist.param:
				par += t[1]
			if len(par) < len('Parameter'):
				lpar = len('Parameter') + 4
			print 'Name'.ljust(lname) + \
				  'Parameter'.ljust(lpar) + \
				  'Start value'.ljust(15) + \
				  'Interval'.ljust(11) + \
				  'Intervals count'
			print '- '*40
			print str(hist.name).ljust(lname) + \
			      str(par).ljust(lpar) + \
			      str(hist.startval).ljust(15) + \
			      str(hist.interval).ljust(11) + \
			      str(hist.count)
			print 
			print '- '*40
			print 'Interval'.ljust(20) + \
			      'Entries'.ljust(11) + \
			      'Percentage'.ljust(15) + \
			      'Histogram'
			print '- '*40
			print ('> '+str(hist.startval)).ljust(20) + \
			      str(hist.intervals[0]).ljust(11) + \
			      '{:.2f}'.format(hist.intervals[0]/float(totalcnt) 
			      * 100).ljust(15) + \
			      '#'*int(hist.intervals[0]/float(totalcnt) * 50)
			for i in range(1, hist.count+1):
				print ('{!s} -- {!s}'.format(
				      hist.startval + hist.interval * (i - 1),
				      hist.startval + hist.interval * i)
				      ).ljust(20) + \
				      str(hist.intervals[i]).ljust(11) + \
				      '{:.2f}'.format(hist.intervals[i]/float(totalcnt)
				      * 100).ljust(15) + \
				      '#'*int(hist.intervals[i]/float(totalcnt) * 50)
			print ('< '+str(hist.startval + hist.interval * 
			      hist.count)).ljust(20) + \
			      str(hist.intervals[-1]).ljust(11) + \
			      '{:.2f}'.format(hist.intervals[-1]/float(totalcnt)
			      * 100).ljust(15) + \
			      '#'*int(hist.intervals[-1]/float(totalcnt) * 50)
		print
		print
			      		
	print '\n\n---- Future events chain: ----'
	if not futureChain:
		print '<<EMPTY>>'
	else:
		lgroup = 0
		for xact in futureChain:
			if len(xact[1].group) > lgroup:
				lgroup = len(xact[1].group)
		if len('Xact group')+4 > lgroup:
			lgroup = len('Xact group')+4
		print 'Move time'.ljust(12) + \
		      'Xact group'.ljust(lgroup+4) + \
		      'Xact ID'.ljust(11) + \
		      'Xact curblock'.ljust(17) + \
		      'Xact status'
		print '- '*45
		for xact in futureChain:
			print str(xact[0]).ljust(12) + \
			      str(xact[1].group).ljust(lgroup+4) + \
			      str(xact[1].index).ljust(11) + \
			      str(xact[1].curblk).ljust(17) + \
			      str(xact[1].cond)
				
	print '\n\n---- Current events chain: ----'
	if not currentChain+tempCurrentChain:
		print '<<EMPTY>>'
	else:
		lgroup = 0
		for xact in currentChain:
			if len(xact.group) > lgroup:
				lgroup = len(xact.group)
		if len('Xact group')+4 > lgroup:
			lgroup = len('Xact group')+4
		else:
			lgroup += 4
		print 'Xact group'.ljust(lgroup) + \
		      'Xact ID'.ljust(11) + \
		      'Xact curblock'.ljust(17) + \
		      'Xact status'
		print '- '*45
		for xact in currentChain+tempCurrentChain:
			print str(xact.group).ljust(lgroup) + \
			      str(xact.index).ljust(11) + \
			      str(xact.curblk).ljust(17) + \
			      str(xact.cond)	  
	print
	print
