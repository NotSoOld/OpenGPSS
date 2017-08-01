##################################################
#    ____                ________  ________      #
#   / __ \___  ___ ___  / ___/ _ \/ __/ __/      #
#  / /_/ / _ \/ -_) _ \/ (_ / ___/\ \_\ \        #
#  \____/ .__/\__/_//_/\___/_/  /___/___/        #
#      /_/           by NotSoOld, 2017 (c)       #
#                                                #
#         route|process|gather stats             #
#                                                #
# interpreter.py - manages program line-by-line  #
# interpreting and xact moving and processing.   #
# All executive blocks are defined here.         #
#                                                #
##################################################



import sys
import os
import random
import copy
import importlib
import lexer
import parser
import structs
import errors
import datetime

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import config

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
graphs = {}
functions = {}
attachables = {}
currentChain = []
tempCurrentChain = []
futureChain = []
xact = None
chxact = None
toklines = []
exitcond = -1
original_stdout = None
logfile = None
results_file = None
file_path = ''

BOLD = '\033[1m'
NORM = '\033[0m'
if (not config.enable_nice_vt100_codes) or config.results_to_file:
	BOLD = ''
	NORM = ''
		
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
	global queues
	if qid not in queues.keys():
		errors.print_error(44, xact.curblk+1, [qid])
	queued = [q[0] for q in queues[qid].queuedxacts]
	if xact.index in queued:
		errors.print_error(39, xact.curblk+1)
	
	if queues[qid].curxacts == 0:
		queues[qid].zero_entries += 1	
	queues[qid].enters_q += 1
	queues[qid].curxacts += 1
	if queues[qid].curxacts > queues[qid].maxxacts:
		queues[qid].maxxacts = queues[qid].curxacts
	queues[qid].queuedxacts.append([xact.index, ints['curticks'].value])
	xact.curblk += 1
	xact.cond = 'canmove'
	toklines[xact.curblk][-1][2] += 1
	
def queue_leave(qid):
	global toklines
	if qid not in queues.keys():
		errors.print_error(44, xact.curblk+1, [qid])
	queued = [q[0] for q in queues[qid].queuedxacts]
	if xact.index not in queued:
		errors.print_error(40, xact.curblk+1)
		
	queues[qid].curxacts -= 1
	index = 0
	enter_time = 0
	for queued_xact in queues[qid].queuedxacts:
		if queued_xact[0] == xact.index:
			enter_time = queued_xact[1]
			break
		index += 1

	del queues[qid].queuedxacts[index]
	time_in_queue = ints['curticks'].value - enter_time
	queues[qid].sum_for_avg_time_in_queue += time_in_queue
	if time_in_queue > queues[qid].max_time_in_queue:
		queues[qid].max_time_in_queue = time_in_queue
	xact.curblk += 1
	xact.cond = 'canmove'
	toklines[xact.curblk][-1][2] += 1
	
def fac_enter(fid, v=1):
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	if facilities[fid].isQueued:
		queued = [q[0] for q in queues[fid].queuedxacts]
		if xact.index not in queued:
			queue_enter(fid)
			toklines[xact.curblk][-1][2] -= 1
			xact.curblk -= 1
		
	if facilities[fid].curplaces - v >= 0 and facilities[fid].isAvail:
		facilities[fid].curplaces -= v
		facilities[fid].enters_f += 1
		if xact.index in facilities[fid].busyxacts:
			errors.print_error(41, xact.curblk+1)
		facilities[fid].busyxacts[xact.index] = [v, ints['curticks'].value]
		
		if config.log_xact_blocking:
			print 'Added xact '+str(xact.index)+' to facility '+fid
		
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
	
	if facilities[fid].maxplaces < vol or not facilities[fid].isAvail:
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
		if config.log_facility_entering:
			print 'added xact '+str(xainfo[0].index)+' back to facility '+fid
		facilities[fid].curplaces += xainfo[2][0]
		facilities[fid].irruptch[i] = []
	facilities[fid].irruptch = [el for el in facilities[fid].irruptch if el != []]
	
def fac_avail(fid):
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	facilities[fid].isAvail = True
	review_cec()
	
def fac_unavail(fid):
	if fid not in facilities.keys():
		errors.print_error(43, xact.curblk+1, [fid])
	facilities[fid].isAvail = False
	move()
	
def wait(time, tdelta=0):
	global futureChain
	global ints
	global toklines
	random.seed()
	futime = ints['curticks'].value + time + random.randint(-tdelta, tdelta)
	xact.curblk += 1
	xact.cond = 'waiting'
	toklines[xact.curblk][-1][2] += 1
	if config.log_FEC_entering:
		print 'Wait(): exit time =', futime
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
	if chid not in chains.keys():
		errors.print_error(48, xact.curblk+1, [chid])

	global toklines
	chains[chid].xacts.append(xact)
	chains[chid].length = len(chains[chid].xacts)
	xact.cond = 'chained'
	toklines[xact.curblk+1][-1][2] += 1
	
def chain_leave(chid, cnt, toblk=''):
	if chid not in chains.keys():
		errors.print_error(48, xact.curblk+1, [chid])

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
	# according to condition (5 or less)
	if chid not in chains.keys():
		errors.print_error(48, xact.curblk+1, [chid])

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
	# chain_find(buf, find(buf.xacts.pr < 10), 5) =>
	# will evaluate condition 5 times
	if chid not in chains.keys():
		errors.print_error(48, xact.curblk+1, [chid])

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
	
def hist_sample(hist, weight=1):
	if hist not in hists.keys():
		errors.print_error(53, xact.curblk+1, [hist])
		
	parser.tokline = hists[hist].param
	parser.pos = 0
	val = parser.parseExpression()
	hists[hist].sample(val, weight)
	move()
	
def graph_sample(graph):
	if graph not in graphs.keys():
		errors.print_error(59, xact.curblk+1, [graph])
		
	parser.tokline = graphs[graph].paramX
	parser.pos = 0
	x = parser.parseExpression()
	parser.tokline = graphs[graph].paramY
	parser.pos = 0
	y = parser.parseExpression()
	graphs[graph].sample(x, y)
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
	global original_stdout
	global logfile
	global results_file
	global file_path
	file_path = filepath
	
	toklines = parser.tocodelines(tokens)
	toklines = parser.convertBlocks(toklines)
	
	logfile = None
	if config.log_to_file:
		name = filepath[:-5]
		now = datetime.dateime.now()
		print 'All logs will be saved in "' + name + \
		      '_log_'+now.strftime("%Y-%m-%d %H:%M")+ \
		      '.txt" file (log file can become very large!).'
		original_stdout = sys.stdout
		logfile = open(name+'_log_'+now.strftime("%Y-%m-%d %H:%M")+'.txt', 'w')
		sys.stdout = logfile
	
	now = datetime.datetime.now()

	print '\n\nSimulating system '+filepath+' at',
	print now.strftime("%Y-%m-%d %H:%M")
	print
	
	if config.print_program_in_tokens:	
		for line in toklines:
			print str(line[-1][0]).zfill(2),
			print line
		print
	
	# Program will be always printed in console, so user can check it 
	# before simulation.
	if original_stdout:
		sys.stdout = original_stdout
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
			dic = globals()[defd[0]+'s']
			if defd[1] in dic.keys():
				errors.print_error(22, lineindex, [defd[1], defd[0]])
			dic[defd[1]] = defd[2]
			withqueue = False
			if defd[0] == 'facilitie' and defd[2].isQueued:
				queues[defd[1]] = structs.Queue(defd[1])
				withqueue = True
			if defd[3]:
				del dic[defd[1]]
				if withqueue:
					del queues[defd[1]]
				turnIntoArray(dic, defd, withqueue)
			
		elif line[0][0] == 'block': 
			if line[0][1] == 'exitwhen':
				if exitcond != -1:
					errors.print_error(23, lineindex)
				exitcond = line[-1][0]
			else:
				errors.print_warning(1, lineindex)
		elif line[0] == ['word', 'attach']:
			attachFileWithFunctions(line)
		else:
			errors.print_warning(1, lineindex)

	anykey = raw_input('Read the info above, it may contain some warnings. ' \
	                   'When ready, press any key')			
	
	if logfile:
		sys.stdout = logfile
	
	for line in toklines:
		if ['block', 'inject'] in line:
			newinj = parser.parseInjector(line)
			injectors[newinj.group] = newinj
			inject(newinj)
			
	while True:
		tempCurrentChain = []
		print '\ntimestep =', ints['curticks'].value
		if config.tick_by_tick_simulation:
			ttt = raw_input()
		
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
			currentChain = sorted(currentChain, 
			                      key=lambda xa: xa.params['priority'])
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
					cmd = parser.parseBlock(toklines[xact.curblk+1])
					if config.log_xact_trace:
						print 'xact', xact.index, 'is about to enter block', \
						       xact.curblk+1, cmd
					if config.block_by_block_simulation:
						ttt = raw_input()
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
							if config.log_xact_blocking:
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
			fac.busyticks += len(fac.busyxacts)/float(fac.maxplaces)
			fac.unweightedbusyticks += len(fac.busyxacts)
			if fac.isAvail:
				fac.avail_time += 1
			else:
				fac.unavail_time += 1
			if fac.maxplaces - fac.curplaces > fac.maxxacts:
				fac.maxxacts = fac.maxplaces - fac.curplaces
		for qu in queues.values():
			qu.sumforavg += qu.curxacts
				
		# Stop modelling.
		if checkExitCond():
			break
	
	count_xacts_on_blocks()
	
	print '\n'*5
	print '='*80
	now = datetime.datetime.now()
	if original_stdout:
		sys.stdout = original_stdout
	if config.results_to_file:
		if not original_stdout:
			original_stdout = sys.stdout
		results_file = open(filepath[:-5]+'_results_'+ \
		                    now.strftime("%Y-%m-%d %H:%M")+'.txt', 'w')
		sys.stdout = results_file
	print_results()
	if results_file:
		sys.stdout = original_stdout
		print 'Simulation finished, results are saved in "' + \
		      filepath[:-5] + '_results_'+now.strftime("%Y-%m-%d %H:%M")+ \
		      '.txt".'

def attachFileWithFunctions(line):
	global attachables
	filename = line[1][1]
	newlib = None
	if filename in attachables:
		errors.print_warning(5, line[-1][0], [filename])
		return
	try:
		newlib = importlib.import_module(filename)
	except ImportError:
		errors.print_error(57, line[-1][0], [filename])
	attachables[filename] = newlib
	
def turnIntoArray(dic, definition, withqueue):
	obj = definition[2]
	name = definition[1]
	if len(definition[3]) == 1:
		# Array
		for i in range(definition[3][0]):
			newname = name+'&&'+str(i)
			obj.name = newname
			dic[newname] = copy.deepcopy(obj)
			if withqueue:
				# It was an auto queued facility array.
				queues[newname] = structs.Queue(newname)
	else:
		# Matrix
		for i in range(definition[3][0]):
			for j in range(definition[3][1]):
				newname = name+'&&('+str(i)+','+str(j)+')'
				obj.name = newname
				dic[newname] = copy.deepcopy(obj)
				if withqueue:
					# It was an auto queued facility array.
					queues[newname] = structs.Queue(newname)
	
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
	
	indent = 0	
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
		prog += '   '*indent
		prevtoken = []
		for token in line:
			t = ''
			if token[0] in lexer.operators.values():
				t = lexer.operators.keys()[lexer.operators.values()
										   .index(token[0])]
				if t == '{' and not prevtoken:
					indent += 1
				elif t == '}' and not prevtoken:
					indent -= 1
					prog = prog[:-3]
				
				if t in ',:':
					t += ' '
				elif t == '{' and prevtoken:
					t = ' '+t
				elif t in '>|?' and prevtoken[0] == 'transport':
					t += ' '
				elif t == '<' and (
				     ['typedef', 'hist'] in line or 
				     ['typedef', 'graph'] in line):
					prog = prog[:-1]
				elif t == '>' and (
				     ['typedef', 'hist'] in line or 
				     ['typedef', 'graph'] in line):
					t += ' '
				elif t == '->' and ['typedef', 'function'] in line:
					t = ' '+t+' ' 
				elif t == '-' and (
				prevtoken[0] == 'word' or prevtoken[0] == 'comma' or
				prevtoken[0] == 'lparen' or prevtoken[0] == 'lbracket' or
				prevtoken[0] == 'lbrace'):
					pass
				elif t in '+,-,*,/,%,**,+=,-=,==,*=,/=,%=,**=,<,>,<=,>=,!=,' \
				          '|,||,&,&&':
					t = ' '+t+' '
				prog += t
			elif token == ['word', 'attach']:
				prog += 'attach '
			elif token[0] == 'word' or \
				 token[0] == 'number' or token[0] == 'block' or \
				 token[0] == 'builtin':
				prog += str(token[1])
			elif token[0] == 'string':
				prog += '"'+token[1]+'"'
			elif token[0] == 'typedef':
				prog += token[1]+' '
			prevtoken = token
		prog += '\n'
	print prog

def print_results():
	BOLD = '\033[1m'
	NORM = '\033[0m'
	if (not config.enable_nice_vt100_codes) or config.results_to_file:
		BOLD = ''
		NORM = ''
	now = datetime.datetime.now()

	print '\n\n'+BOLD+'SIMULATION RESULTS OF SYSTEM '+file_path+NORM
	print '\nSimulation finished at',
	print now.strftime("%Y-%m-%d %H:%M")
	
	print '\n\n\n'+BOLD+'-------- Generated program: --------\n'+NORM+ \
	      '(line index, current xacts, total executions, line of code)\n'
	print_program()
	print BOLD+'\nSimulation time: '+NORM+str(ints['curticks'].value)+' beats'
	
	if attachables.keys():
		print BOLD+'\nAttached modules:'+NORM,
		print attachables.keys()[0],
		for att in attachables.keys()[1:]:
			print ', '+att,
	
	if ints.keys():
		print '\n\n'+BOLD+'-------- Integer variables: --------\n'+NORM
		print_vars_arrays_and_matrices(ints)				
	
	if floats.keys():
		print '\n\n\n'+BOLD+'-------- Float variables: --------\n'+NORM
		print_vars_arrays_and_matrices(floats, 'f')
			
	if strs.keys():
		print '\n\n\n'+BOLD+'-------- String variables: --------\n'+NORM
		print_vars_arrays_and_matrices(strs)
		
	if bools.keys():
		print '\n\n\n'+BOLD+'-------- Boolean variables: --------\n'+NORM
		print_vars_arrays_and_matrices(bools)
	
	global facilities
	print '\n\n\n'+BOLD+'-------- Facilities: --------'+NORM
	if not facilities.keys():
		print '\n<<NO FACILITIES>>'
	else:
		for fac in facilities.values():
			if '&&(' in fac.name:
				fac.name = fac.name[:-1].replace('&&(', '[[') + ']]'
			elif '&&' in fac.name:
				fac.name = fac.name.replace('&&', '[') + ']'
		facilities = sorted(facilities.values(), key=lambda x: x.name)
		lname = 0
		for fac in facilities:
			if len(fac.name) > lname:
				lname = len(fac.name)
		print ''.ljust(lname+5+10+13+14+11) + \
		      'Busyness'.ljust(15) + \
		      'Busyness'.ljust(15) + \
		      'Current xacts'
		print 'Name'.ljust(lname+5) + \
		      'Places'.ljust(10) + \
		      'Max xacts'.ljust(13) + \
		      'Auto queued'.ljust(14) + \
		      'Enters'.ljust(11) + \
		      '(weighted)'.ljust(15) + \
		      '(unweighted)'.ljust(15) + \
		      '(index: [vol, enter time])'
		print '- '*55
		for fac in facilities:
			print str(fac.name).ljust(lname+5) + \
			      str(fac.maxplaces).ljust(10) + \
			      str(fac.maxxacts).ljust(13) + \
			      str(fac.isQueued).ljust(14) + \
			      str(fac.enters_f).ljust(11) + \
			      ('{:.3f}'.format(fac.busyticks/float(ints['curticks']
			      .value)).ljust(15)) + \
			      ('{:.3f}'.format(fac.unweightedbusyticks/float(ints['curticks']
			      .value)).ljust(15)) + \
			      str(fac.busyxacts)
		#print '- '*55
		print '\n'
		print 'Average'.ljust(19) + \
		      ''.ljust(14+14+16) + \
		      'Availa-'.ljust(13) + \
		      'Irrupted'.ljust(12)
		print 'processing time'.ljust(19) + \
		      'Is available'.ljust(14) + \
		      'Avail. time'.ljust(14) + \
		      'Unavail. time'.ljust(16) + \
		      'bility (%)'.ljust(13) + \
		      'xacts'.ljust(12) + \
		      'Irrupt chain'
		print '- '*55
		for fac in facilities:
			print ('{:.2f}'.format(fac.processedxactsticks/float(
			      fac.enters_f - (fac.maxplaces - fac.curplaces)))).ljust(19) + \
			      str(fac.isAvail).ljust(14) + \
			      str(fac.avail_time).ljust(14) + \
			      str(fac.unavail_time).ljust(16) + \
			      ('{:.2f}'.format(fac.avail_time / float(fac.avail_time + \
			      fac.unavail_time) * 100)).ljust(13) + \
			      str(len(fac.irruptch)).ljust(12) + \
			      str(fac.irruptch)
	
	global queues
	print '\n\n\n'+BOLD+'-------- Queues: --------\n'+NORM
	if not queues.keys():
		print '<<NO QUEUES>>'
	else:
		for qu in queues.values():
			if '&&(' in qu.name:
				qu.name = qu.name[:-1].replace('&&(', '[[') + ']]'
			elif '&&' in qu.name:
				qu.name = qu.name.replace('&&', '[') + ']'
		lname = 0
		queues = sorted(queues.values(), key=lambda x: x.name)
		for qu in queues:
			if len(qu.name) > lname:
				lname = len(qu.name)
		print 'Name'.ljust(lname+5) + \
		      'Enters'.ljust(10) + \
		      'Zero entries'.ljust(15) + \
		      'Zero entries (%)'.ljust(18) + \
		      'Max length'.ljust(13) + \
		      'Avg length'.ljust(13) + \
		      'Current length'
		print '- '*55
		for qu in queues:
			print str(qu.name).ljust(lname+5) + \
			      str(qu.enters_q).ljust(10) + \
			      str(qu.zero_entries).ljust(15) + \
			      ('{:.2f}'.format(qu.zero_entries / 
			      float(qu.enters_q) * 100)).ljust(18) + \
			      str(qu.maxxacts).ljust(13) + \
			      ('{:.2f}'.format(qu.sumforavg/float(ints['curticks']
			      .value)).ljust(13)) + \
			      str(qu.curxacts).ljust(19)
		#print '- '*55
		print '\n'
		print 'Avg xact'.ljust(12) + \
		      'Avg xact wait time'.ljust(24) + \
		      'Max xact'.ljust(12) + \
		      'Current queue contents'
		print 'wait time'.ljust(12) + \
		      '(w/o zero entries)'.ljust(24) + \
		      'wait time'.ljust(12) + \
		      '[index, enter time]'
		print '- '*55
		for qu in queues:
			avg_wo_zero = ''
			if qu.enters_q - qu.curxacts - qu.zero_entries == 0:
				avg_wo_zero = '(no data)'
			else:
				avg_wo_zero = '{:.2f}'.format(qu.sum_for_avg_time_in_queue / 
					  float(qu.enters_q - qu.curxacts - qu.zero_entries))
			print ('{:.2f}'.format(qu.sum_for_avg_time_in_queue / 
			      float(qu.enters_q - qu.curxacts))).ljust(12) + \
			      avg_wo_zero.ljust(24) + \
			      str(qu.max_time_in_queue).ljust(12) + \
			      str(qu.queuedxacts)
	
	global chains			  
	print '\n\n\n'+BOLD+'-------- User chains: --------\n'+NORM
	if not chains.keys():
		print '<<NO USER CHAINS>>'
	else:
		for ch in chains.values():
			if '&&(' in ch.name:
				ch.name = ch.name[:-1].replace('&&(', '[[') + ']]'
			elif '&&' in ch.name:
				ch.name = ch.name.replace('&&', '[') + ']'
		chains = sorted(chains.values(), key=lambda x: x.name)
		lname = 0
		for ch in chains:
			if len(ch.name) > lname:
				lname = len(ch.name)
		print 'Name'.ljust(lname+5) + \
		      'Current length'.ljust(19) + \
		      'Current xacts (indexes)'
		print '- '*40
		for ch in chains:
			print str(ch.name).ljust(lname+5) + \
			      str(ch.length).ljust(19) + \
			      str([xa.index for xa in ch.xacts])
	
	global marks
	marks = {k:v for k,v in marks.items() if not k.startswith('&')}
	if marks.keys():
		print '\n\n\n'+BOLD+'-------- Marks: --------\n'+NORM
		lname = 0
		marks = sorted(marks.values(), key=lambda x: x.name)
		for mark in marks:
			if len(mark.name) > lname:
				lname = len(mark.name)
		print 'Name'.ljust(lname+5) + \
		      'Corresponding line'
		print '- '*40
		for mark in marks:
			print str(mark.name).ljust(lname+5) + \
			      str(mark.block)
	
	global hists
	if hists.keys():
		print '\n\n\n'+BOLD+'-------- Histograms: --------\n'+NORM
		for hist in hists.values():
			if '&&(' in hist.name:
				hist.name = hist.name[:-1].replace('&&(', '[[') + ']]'
			elif '&&' in hist.name:
				hist.name = hist.name.replace('&&', '[') + ']'
		hists = sorted(hists.values(), key=lambda x: x.name)
		for hist in hists:
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
				  'Intervals count'.ljust(19) + \
				  'Total entries'.ljust(18) + \
				  'Avg value'
			print '- '*40
			print str(hist.name).ljust(lname) + \
			      str(par).ljust(lpar) + \
			      str(hist.startval).ljust(15) + \
			      str(hist.interval).ljust(11) + \
			      str(hist.count).ljust(19) + \
			      str(hist.enters_h).ljust(18) + \
			      '{:.3f}'.format(hist.average)
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
			      '*'*int(hist.intervals[0]/float(totalcnt) * 50)
			for i in range(1, hist.count+1):
				print ('{!s} -- {!s}'.format(
				      hist.startval + hist.interval * (i - 1),
				      hist.startval + hist.interval * i)
				      ).ljust(20) + \
				      str(hist.intervals[i]).ljust(11) + \
				      '{:.2f}'.format(hist.intervals[i]/float(totalcnt)
				      * 100).ljust(15) + \
				      '*'*int(hist.intervals[i]/float(totalcnt) * 50)
			print ('< '+str(hist.startval + hist.interval * 
			      hist.count)).ljust(20) + \
			      str(hist.intervals[-1]).ljust(11) + \
			      '{:.2f}'.format(hist.intervals[-1]/float(totalcnt)
			      * 100).ljust(15) + \
			      '*'*int(hist.intervals[-1]/float(totalcnt) * 50)
		print
		print
		
	global graphs	
	if graphs.keys():
		print BOLD+'\n\n\n-------- 2D Graphs\' (value tables): --------\n'
		for gr in graphs.values():
			if '&&(' in gr.name:
				gr.name = gr.name[:-1].replace('&&(', '[[') + ']]'
			elif '&&' in gr.name:
				gr.name = gr.name.replace('&&', '[') + ']'
		graphs = sorted(graphs.values(), key=lambda x: x.name)
		for gr in graphs:
			print '-Graph "'+gr.name+'":'
			print 'X'.ljust(20) + 'Y'
			# sort values dictionary and print
			sorted_values = sorted(gr.values.items(), key=lambda x: x[0])
			print '- '*20
			for v in sorted_values:
				print ('{:.4f}'.format(v[0])).ljust(20) + '{:.4f}'.format(v[1])
			print '\n'
			      		
	print '\n\n\n'+BOLD+'-------- Future events chain: --------\n'+NORM
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
				
	print '\n\n\n'+BOLD+'-------- Current events chain: --------\n'+NORM
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
	print '\n'*2
	print '='*80
	
def print_vars_arrays_and_matrices(dic, flag=''):
	onlyvars = [var for var in dic.values() 
		            if '&&' not in var.name]

	matrices = [matrix for matrix in dic.values()
	            if '&&(' in matrix.name]
	            
	arrays = [array for array in ints.values() 
	            if '&&' in array.name and '&&(' not in array.name]

	onlyvars = sorted(onlyvars, key=lambda x: x.name)
	for var in arrays:
		var.name = var.name.replace('&&', '[') + ']'
	arrays = sorted(arrays, key=lambda x: x.name)
	
	for var in matrices:
		var.name = var.name[:-1].replace('&&(', '[[') + ']]'
	matrices = sorted(matrices, key=lambda x: x.name)
		
	lname = 0
	lvalue = 0
	for var in onlyvars+arrays+matrices:
		if flag == 'f':
			var.value = round(var.value, 3)
		if len(var.name) > lname:
			lname = len(var.name)
		if len(str(var.value)) > lvalue:
			lvalue = len(str(var.value))
	print 'Name'.ljust(lname+3) + 'Value'
	print '- '*30
	for var in onlyvars:
		print var.name.ljust(lname+3) + str(var.value)
	
	print
	if arrays:
		prevname = ''
		for arr in arrays:
			trunc_name = arr.name.partition('[')[0]
			if prevname != trunc_name:
				if prevname != '':
					print ' ]'
				sys.stdout.write(trunc_name.ljust(lname) + '[ ' + str(arr.value))
				sys.stdout.flush()
			else:
				sys.stdout.write(', ' + str(arr.value))
				sys.stdout.flush()
			prevname = trunc_name
		print ' ]'
		print
	
	if matrices:
		prevname = ''
		prevline = -1
		for mx in matrices:
			trunc = mx.name.partition('[[')[0]
			line = int(mx.name.partition('[[')[2].partition(',')[0])
		
			if prevname != trunc or prevname == '':
				if prevname != '':
					# It's not the first matrix.
					print '] ]\n'
				# New matrix started.
				print trunc.ljust(lname) + '[ [ ' + str(mx.value).ljust(lvalue),
				prevline = line
				prevname = trunc
			else:
				if prevline != line:
					# New line started.
					print ']'
					print ''.ljust(lname+2) + '[ ' + str(mx.value).ljust(lvalue),
					prevline = line
				else:
					print '   '+str(mx.value).ljust(lvalue),
		print '] ]'
		
def print_logo():
	print """
     ____                ________  ________
    / __ \___  ___ ___  / ___/ _ \/ __/ __/
   / /_/ / _ \/ -_) _ \/ (_ / ___/\ \_\ \  
   \____/ .__/\__/_//_/\___/_/  /___/___/  
       /_/           by NotSoOld, 2017 (c)                      
   
          route|process|gather stats

===============================================

"""
