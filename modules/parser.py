import sys
import structs
import interpreter
import errors
import builtins

pos = 0
tokline = []
lineindex = 0
assgs = [
         'eq', 
         'add', 
         'subt', 
         'inc', 
         'dec', 
         'multeq', 
         'diveq', 
         'remaineq', 
         'pwreq'
        ]
fac_params = [
              'curplaces',
              'maxplaces',
              'enters_f'
             ]
queue_params = [
                'curxacts',
                'enters_q'
               ]
chain_params = [
                'length'
               ]
xact_params = [
               'group',
               'index'
              ]
             
def tocodelines(program):
	parsed = []
	i = 0
	while i < len(program):
		token = program[i]
		if token[0] in 'lbrace'+'rbrace'+'lexec'+'rexec':
			parsed.append([token])
			i += 1
			continue

		line = []
		while True:
			token = program[i]
			line.append(token)
			i += 1
			if token[0] == 'eocl':
				parsed.append(line)
				break
			if i >= len(program):
				errors.print_error(2, '')
	return parsed

def parseDefinition(line):
	global pos
	global tokline
	pos = 0
	tokline = line
	name = ''
	newobj = None
	deftype = line[0][1]
	global lineindex
	lineindex = interpreter.toklines.index(line)+1
	
	tok = nexttok()
	if not tok or tok[0] != 'word':
	   errors.print_error(3, lineindex, tok)
	name = tok[1]
	
	tok = nexttok()
	if deftype == 'int':
		if tok[0] == 'eocl':
			newobj = structs.IntVar(name, 0)
		elif tok[0] == 'eq':
			nexttok()
			newobj = structs.IntVar(name, parseExpression())
		else:
			errors.print_error(12, lineindex, ['=', peek(0)])
		
	elif deftype == 'float':
		if tok[0] == 'eocl':
			newobj = structs.FloatVar(name, 0)
		elif tok[0] == 'eq':
			nexttok()
			newobj = structs.FloatVar(name, parseExpression())
		else:
			errors.print_error(12, lineindex, ['=', peek(0)])
			
	elif deftype == 'bool':
		if tok[0] == 'eocl':
			newobj = structs.BoolVar(name, 0)
		elif tok[0] == 'eq':
			nexttok()
			newobj = structs.BoolVar(name, parseExpression())
		else:
			errors.print_error(12, lineindex, ['=', peek(0)])
			
	elif deftype == 'fac':
		if tok[0] == 'eocl':
			newobj = structs.Facility(name, 1, True)
			# Note: let the interpreter create a queue for facility.
		elif matchtok('lbrace'):
			isQueued = True
			places = 1
			while True:
				if matchtok('rbrace'):
					break
				if matchtok('comma'):
					continue
				if matchtok('word', 'places'):
					consume('eq')
					tok = peek(0)
					try:
						places = int(tok[1])
					except ValueError:
						errors.print_error(5, lineindex, 
						       ['int', 'places', tok])
					nexttok()
					continue
				if matchtok('word', 'isQueued'):
					consume('eq')
					tok = peek(0)
					if tok[1] == 'true':
						isQueued = True
					elif tok[1] == 'false':
						isQueued = False
					else:
						errors.print_error(5, lineindex, 
						       ['bool', 'isQueued', tok[1]])
					nexttok()
					continue
				errors.print_error(4, lineindex, [peek(0)])
			newobj = structs.Facility(name, places, isQueued)
			deftype = 'facilitie'
		else:
			errors.print_error(12, lineindex, ['{', peek(0)])
		
	elif deftype == 'queue':
		newobj = structs.Queue(name)
	
	elif deftype == 'chain':
		newobj = structs.Chain(name)
		
	elif deftype == 'mark':
		newobj = structs.Mark(name, -1)
		for line in interpreter.toklines:
			if line[0] == ['word', name] and line[1][0] == 'marksep':
				if newobj.block != -1:
					i = interpreter.toklines.index(line)
					errors.print_error(13, i+1, [name])
				newobj.block = interpreter.toklines.index(line)
		if newobj.block == -1:
			errors.print_warning(3, '', [name])
			
	elif deftype == 'str':
		if tok[0] == 'eocl':
			newobj = structs.StrVar(name, '')
		elif tok[0] == 'eq':
			nexttok()
			newobj = structs.StrVar(name, parseExpression())
		else:
			errors.print_error(12, lineindex, ['=', peek(0)])
			
	else: # If deftype is fac_enum
		pass
	
	return (deftype, name, newobj)

def parseBlock(line):
	global tokline
	global pos
	tokline = line
	pos = 0
	name = ''
	args = []
	global lineindex
	lineindex = interpreter.toklines.index(line)+1
	
	if ['rexec', ''] in tokline:
		errors.print_error(14, lineindex)
	if peek(0)[0] == 'word' and peek(1)[0] == 'marksep':
		if peek(0)[1] in interpreter.marks:
			consume('word')
			consume('marksep')
		else:
			errors.print_error(15, lineindex, [peek(0)[1]])

	tok = peek(0)
	if tok[0] == 'word':
		"""tok1 = peek(1)
		tok2 = peek(2)
		tok3 = peek(3)
		prim = ''
		sec = ''
		assg = ''
		key = ''
		
		if tok1[0] == 'dot' and tok2[0] == 'word':
			nexttok()
			nexttok()
			if tok[1] == 'xact':
				prim = 'xact'
				if tok2[1] not in interpreter.xact.params.keys():
					errors.print_error(25, lineindex, 
					       [interpreter.xact.group, tok2[1]])
				sec = 'params'
				key = tok2[1]
			else:
				errors.print_error(26, lineindex, [tok[1]])
			assg = tok3[0]
			
			evaluateAssignment(prim, sec, assg, key)
			
		else:
			if tok[1] in interpreter.ints:
				prim = 'ints'
			elif tok[1] in interpreter.floats:
				prim = 'floats'
			elif tok[1] in interpreter.strs:
				prim = 'strs'
			elif tok[1] in interpreter.bools:
				prim = 'bools'
			else:
				errors.print_error(27, lineindex, [tok[1]])
			key = tok[1]
			assg = tok1[0]
			
			evaluateAssignment(prim, '', assg, key)
			
		return ('move', [])"""
		return parseAssignment()
	
	elif tok[0] == 'rbrace':
		depth = 0
		for i in reversed(range(0, xact.curblk+2)):
			if interpreter.toklines[i][0][0] == 'rbrace':
				depth += 1
			elif interpreter.toklines[i][0][0] == 'lbrace':
				depth -= 1
			if depth == 0:
				break
		if depth != 0:
			errors.print_error(38, '', ['}', xact.curblk+2])
		i -= 1
		if ['block', 'while'] in interpreter.toklines[i]:
			xact.curblk = i - 1
			xact.cond = 'canmove'
			return parseBlock(interpreter.toklines[i])
	
	elif tok[0] == 'block':
		if tok[1] == 'inject':
			name = 'move'
		else:
			name = tok[1]
			if tok[1] == 'if' or tok[1] == 'else_if' or \
			   tok[1] == 'else' or tok[1] == 'try' or \
			   tok[1] == 'while' or tok[1] == 'for':
				name += '_block'
			nexttok()
			consume('lparen')
			while True:
				if matchtok('rparen'):
					break
				args.append(parseExpression())
				if peek(0)[0] == 'comma':
					consume('comma')
					continue
				elif peek(0)[0] == 'rparen':
					consume('rparen')
					break;
				else:
					errors.print_error(16, lineindex, [peek(0)])
		return (name, args)
	
	elif tok[0] == 'transport':
		nexttok()
		if matchtok('gt'):
			name = 'transport'
		elif matchtok('transport_prob'):
			name = 'transport_prob'
		elif matchtok('transport_if'):
			name = 'transport_if'
		else:
			errors.print_error(34, lineindex, [peek(1)])
		block = parseExpression()
		if not matchtok('comma'):
			if name != 'transport':
				errors.print_error(35, lineindex)
			return (name, [block])
		prob = parseExpression()
		if matchtok('comma'):
			additblock = parseExpression()
			return (name, [block, prob, additblock])
		else:
			return (name, [block, prob])
	
	else:
		errors.print_error(21, lineindex, ['executive block, '\
		       'transport operator or assignment lvalue', tok], 'E')

def parseAssignment():
	tok = peek(0)
	tok1 = peek(1)
	tok2 = peek(2)
	tok3 = peek(3)
	prim = ''
	sec = ''
	assg = ''
	key = ''
	res = ()
	
	if tok1[0] == 'dot' and tok2[0] == 'word':
		nexttok()
		nexttok()
		if tok[1] == 'xact':
			prim = 'xact'
			if tok2[1] not in interpreter.xact.params.keys():
				errors.print_error(25, lineindex, 
				       [interpreter.xact.group, tok2[1]])
			sec = 'params'
			key = tok2[1]
		else:
			errors.print_error(26, lineindex, [tok[1]])
		assg = tok3[0]
		
		res = evaluateAssignment(prim, sec, assg, key)
		
	else:
		if tok[1] in interpreter.ints:
			prim = 'ints'
		elif tok[1] in interpreter.floats:
			prim = 'floats'
		elif tok[1] in interpreter.strs:
			prim = 'strs'
		elif tok[1] in interpreter.bools:
			prim = 'bools'
		else:
			errors.print_error(27, lineindex, [tok[1]])
		key = tok[1]
		assg = tok1[0]
		
		res = evaluateAssignment(prim, '', assg, key)
		
	return res

def evaluateAssignment(prim, sec, assg, key):
	global assgs
	global lineindex
	#prim = xact, ints[], floats[], strs[]
	#sec = '', params[]
	#key = dict key if prim==ints,floats,strs and sec=='' - .value
	   #or dict key/'pr' if prim==xact and sec==params - []directly
	#print prim, sec, assg, key
	if assg in assgs:
		attr = getattr(interpreter, prim)
		if sec != '': # xact.params[key]
			attr = getattr(attr, sec)
			if assg == 'inc':
				if type(attr[key]) is str or type(attr[key]) is bool:
					errors.print_error(7, lineindex, ['inc'])
				attr[key] += 1
			elif assg == 'dec':
				if type(attr[key]) is str or type(attr[key]) is bool:
					errors.print_error(7, lineindex, ['dec'])
				attr[key] -= 1
			else:
				nexttok()
				nexttok()
				result = parseExpression()
				result = checkAssignmentTypes(attr[key], result, assg)
			   	if assg == 'eq':         attr[key] = result
			   	elif assg == 'add':      attr[key] += result
			   	elif assg == 'subt':     attr[key] -= result
			   	elif assg == 'multeq':   attr[key] *= result
			   	elif assg == 'diveq':    attr[key] /= result
			   	elif assg == 'pwreq':    attr[key] = attr[key] ** result
			   	elif assg == 'remaineq': attr[key] %= result
			   	
		else: # ints[key].value, etc.
			if assg == 'inc':
				if type(attr[key].value) is str or type(attr[key].value) is bool:
					errors.print_error(7, lineindex, ['inc'])
				attr[key].value += 1
			elif assg == 'dec':
				if type(attr[key].value) is str or type(attr[key].value) is bool:
					errors.print_error(7, lineindex, ['dec'])
				attr[key].value -= 1
			else:
				nexttok()
				nexttok()
				result = parseExpression()
				result = checkAssignmentTypes(attr[key].value, result, assg)
			   	if assg == 'eq':         attr[key].value = result
			   	elif assg == 'add':      attr[key].value += result
			   	elif assg == 'subt':     attr[key].value -= result
			   	elif assg == 'multeq':   attr[key].value *= result
			   	elif assg == 'diveq':    attr[key].value /= result
			   	elif assg == 'pwreq':
			   		attr[key].value = attr[key].value ** result
			   	elif assg == 'remaineq': attr[key].value %= result
		
		if prim == 'xact' and sec == 'params' and key == 'pr':
			return ('review_cec', [])	
		return ('move', [])
	else:
		errors.print_error(21, lineindex, 
			   ['assignment operator or "."', tok], 'C')

def checkAssignmentTypes(l, r, asg):
	if type(l) is int:
		if type(r) is int:
			return r
		if type(r) is float:
			return int(r)
		errors.print_error(33, lineindex, [asg, type(l), type(r)])
	if type(l) is float:
		if type(r) is int or type(r) is float:
			return r
		errors.print_error(33, lineindex, [asg, type(l), type(r)])
	if type(l) is str:
		if type(r) is not str:
			errors.print_error(33, lineindex, [asg, type(l), type(r)])
		if asg != 'eq' and asg != 'add':
			errors.print_error(33, lineindex, [asg, type(l), type(r)])
		return r
	if type(l) is bool:
		if type(r) is not bool:
			errors.print_error(33, lineindex, [asg, type(l), type(r)])
		return r
		
def parseInjector(line):
	newinj = None
	global tokline
	global pos
	pos = 0
	tokline = line
	global lineindex
	lineindex = interpreter.toklines.index(line)+1
	
	if peek(0)[0] == 'word' and peek(1)[0] == 'marksep':
		if peek(0)[1] in interpreter.marks:
			consume('word')
			consume('marksep')
		else:
			errors.print_error(15, lineindex, [peek(0)[1]])
	
	consume('block', 'inject')
	consume('lparen')
	
	tok = peek(0)
	if tok[0] != 'string':
		errors.print_error(17, lineindex, [tok])
	group = tok[1]
	nexttok()
	consume('comma')
	args = []
	for i in range (0, 4):
		tok = peek(0)
		if tok[0] != 'number':
			errors.print_error(18, lineindex, [tok])
		args.append(int(tok[1]))
		nexttok()
		if i != 3:
			consume('comma')
		else:
			consume('rparen')
			
	blk = interpreter.toklines.index(line)
	if not matchtok('lbrace'):
		newinj = structs.Injector(group, args[0], args[1], args[2], args[3], blk)
		return newinj
	params = {}
	while True:
		if matchtok('rbrace'):
			break
		if matchtok('comma'):
			continue
		tok1 = peek(0)
		nexttok()
		consume('eq')
		tok2 = peek(0)
		
		if tok1[1] == 'priority':
			if tok2[0] != 'number':
				errors.print_error(19, lineindex, ['number', tok1[1], tok2])
			params['pr'] = float(tok2[1])
			
		elif tok1[1].startswith('p'):
			if tok2[0] != 'number' or '.' in tok2[1]:
				errors.print_error(19, lineindex, ['integer', tok1[1], tok2])
			params[tok1[1]] = int(tok2[1])
			
		elif tok1[1].startswith('b'):
			if tok2[0] != 'word' or tok2[1] != 'true' and tok2[1] != 'false':
				errors.print_error(19, lineindex, ['boolean', tok1[1], tok2])
			if tok2[1] == 'true':
				params[tok1[1]] = True
			else:
				params[tok1[1]] = False
			
		elif tok1[1].startswith('f'):
			if tok2[0] != 'number':
				errors.print_error(19, lineindex, ['number', tok1[1], tok2])
			params[tok1[1]] = float(tok2[1])
			
		elif tok1[1].startswith('str'):
			if tok2[0] != 'string':
				errors.print_error(19, lineindex, ['string', tok1[1], tok2])
			params[tok1[1]] = tok2[1]
			
		else:
			errors.print_warning(2, lineindex, [tok1[1]])
			params[tok1[1]] = tok2[1]
		nexttok()
		
	newinj = structs.Injector(group, args[0], args[1], args[2], args[3], blk, params)
	return newinj
	
def parseExitCondition(line):
	global tokline
	global pos
	pos = 0
	tokline = line
	nexttok()
	consume('lparen')
	result = parseExpression()
	consume('rparen')
	if result == 0:
		return False
	return True

def parseExpression():
	result = parseLogicalOr()
	return result

def parseLogicalOr():
	result = parseLogicalAnd()
	while True:
		if matchtok('or'):
			result = result or parseLogicalAnd()
			continue
		break
	return result

def parseLogicalAnd():
	result = parseCompEq()
	while True:
		if matchtok('and'):
			result = result and parseCompEq()
			continue
		break
	return result
	
def parseCompEq():
	result = parseCondition()
	while True:
		if matchtok('compeq'):
			result = result == parseCondition()
			continue
		if matchtok('noteq'):
			result = result != parseCondition()
			continue
		break
	return result
	
def parseCondition():
	result = parseAdd()
	while True:
		if matchtok('gt'):
			result = result > parseAdd()
			continue
		if matchtok('less'):
			result = result < parseAdd()
			continue
		if matchtok('gteq'):
			result = result >= parseAdd()
			continue
		if matchtok('lesseq'):
			result = result <= parseAdd()
			continue
		break
	return result
	
def parseAdd():
	result = parseMult()
	
	while True:
		if matchtok('plus'):
			result1 = parseMult()
			if type(result1) is str and type(result) is not str or \
			   type(result) is str and type(result1) is not str:
				errors.print_error(20, lineindex)
			result += result1
			continue
		if matchtok('minus'):
			result1 = parseMult()
			if type(result1) is str or type(result) is str:
				errors.print_error(8, lineindex, ['-'])
			result -= result1
			continue
		break
	
	return result
	
def parseMult():
	result = parseUnary()
	
	while True:
		if matchtok('mult'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				errors.print_error(8, lineindex, ['*'])
			result *= result1
			continue
		if matchtok('div'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				errors.print_error(8, lineindex, ['/'])
			result /= result1
			continue
		if matchtok('remain'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				errors.print_error(8, lineindex, ['%'])
			result = result % result1
			continue
		if matchtok('pwr'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				errors.print_error(8, lineindex, ['**'])
			result = result ** result1
			continue
		break
	
	return result
	
def parseUnary():
	if matchtok('not'):
		return (not parsePrimary())
	if matchtok('minus'):
		return -1 * parsePrimary()
	if matchtok('plus'):
		return parsePrimary()
	return parsePrimary()
	
def parsePrimary():
	if matchtok('lparen'):
		result = parseExpression()
		consume('rparen')
		return result
	tok = peek(0)
	val = 0
	if tok[0] == 'number':
		if '.' in tok[1]:
			val = float(tok[1])
		else:
			val = int(tok[1])
	elif tok[0] == 'string':
		val = tok[1]
	elif tok[0] == 'word':
		if tok[1] == 'true':
			val = True
		elif tok[1] == 'false':
			val = False
		elif peek(1)[0] == 'dot':
			nexttok()
			consume('dot')
			tk = peek(0)
			if tk[1] in fac_params and tok[1] in interpreter.facilities:
				val = getattr(interpreter.facilities[tok[1]], tk[1])
				
			elif tk[1] in queue_params and tok[1] in interpreter.queues:
				val = getattr(interpreter.queues[tok[1]], tk[1])
				
			elif tk[1] in queue_params and tok[1] in interpreter.chains:
				val = getattr(interpreter.chains[tok[1]], tk[1])
			
			elif tok[1] == 'xact':
				if tk[1] not in xact_params: #parameters from 'params' dict
					if tk[1] not in interpreter.xact.params.keys():
						errors.print_error(25, lineindex, 
						       [interpreter.xact.group, tk[1]])
					val = interpreter.xact.params[tk[1]]
						
				else: #direct parameters
					val = getattr(interpreter.xact, tk[1])
			
			elif tk[1] == 'name':
				if tok[1] in interpreter.ints:
					val = interpreter.ints[tok[1]].name
				elif tok[1] in interpreter.floats:
					val = interpreter.floats[tok[1]].name
				elif tok[1] in interpreter.strs:
					val = interpreter.strs[tok[1]].name
				elif tok[1] in interpreter.bools:
					val = interpreter.bools[tok[1]].name
				else:
					errors.print_error(28, lineindex, [tok[1]])
			else:
				errors.print_error(21, lineindex, 
				       ["name of parameter of defined variable", tok[1]], 'B')
			nexttok()	
			return val
		
		# If there is no dot:
		elif tok[1] in interpreter.ints:
			val = interpreter.ints[tok[1]].value
		elif tok[1] in interpreter.floats:
			val = interpreter.floats[tok[1]].value
		elif tok[1] in interpreter.strs:
			val = interpreter.strs[tok[1]].value
		elif tok[1] in interpreter.bools:
			val = interpreter.bools[tok[1]].value
		elif tok[1] in interpreter.facilities:
			val = interpreter.facilities[tok[1]].name
		elif tok[1] in interpreter.queues:
			val = interpreter.queues[tok[1]].name
		elif tok[1] in interpreter.marks:
			val = interpreter.marks[tok[1]].name
		elif tok[1] in interpreter.chains:
			val = interpreter.chains[tok[1]].name
		else:
			errors.print_error(6, lineindex, tok)
	
	elif tok[0] == 'builtin':
		return parseBuiltin()
	
	nexttok()
	return val

def parseBuiltin():
	fun = getattr(builtins, peek(0)[1])
	nexttok()
	nexttok()
	return fun(parseExpression())

def consume(toktype, toktext=''):
	global pos
	global lineindex
	if peek(0)[0] != toktype:
		if toktext != '':
			if peek(0)[1] != toktext:
				errors.print_error(21, lineindex, 
				       [[toktype, toktext], peek(0)], 'A')
		else:
			errors.print_error(21, lineindex, 
				       [toktype, peek(0)], 'A')
	pos += 1
	
def nexttok():
	global pos
	global tokline
	pos += 1
	if pos >= len(tokline):
		return []
	return tokline[pos]

def matchtok(toktype, toktext=''):
	global pos
	if peek(0)[0] != toktype or peek(0)[1] != toktext:
		return False
	pos += 1
	return True
	
def peek(relpos):
	global pos
	global tokline
	index = pos + relpos
	if len(tokline) <= index:
		return []
	return tokline[index]
