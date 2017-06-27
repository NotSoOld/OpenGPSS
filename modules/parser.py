import sys
import structs
import interpreter
import errors

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
              'maxplaces'
             ]
queue_params = [
                'curxacts'
               ]
xact_params = [
               'group',
               'index',
               'pr'
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
		if not tok:
			newobj = structs.IntVar(name, 0)
		elif tok[0] == 'eq':
			nexttok()
			newobj = structs.IntVar(name, parseExpression())
		
	elif deftype == 'float':
		if not tok:
			newobj = structs.FloatVar(name, 0)
		elif tok[0] == 'eq':
			nexttok()
			newobj = structs.FloatVar(name, parseExpression())
			
	elif deftype == 'fac':
		if not tok:
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
						errors.print_error(5, lineindex, ['int', 'places', tok])
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
						errors.print_error(5, lineindex, ['bool', 'isQueued', tok[1]])
					nexttok()
					continue
				errors.print_error(4, lineindex, [peek(0)])
			newobj = structs.Facility(name, places, isQueued)
			deftype = 'facilitie'
		else:
			errors.print_error(12, lineindex, [peek(0)])
		
	elif deftype == 'queue':
		newobj = structs.Queue(name)
	
	elif deftype == 'chain':
		pass
	elif deftype == 'mark':
		newobj = structs.Mark(name, -1)
		for line in interpreter.toklines:
			if line[0] == ['word', name] and line[1][0] == 'marksep':
				if newobj.block != -1:
					i = interpreter.toklines.index(line)
					errors.print_error(13, i+1, [name])
				newobj.block = interpreter.toklines.index(line)
			
		
	elif deftype == 'str':
		if not tok:
			newobj = structs.StrVar(name, '')
		elif tok[0] == 'eq':
			nexttok()
			newobj = structs.StrVar(name, parseExpression())
			
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
	if peek(0)[0] == 'word':
		if peek(0)[1] in interpreter.marks:
			consume('word', )
		else:
			errors.print_error(15, lineindex, [peek(0)[1]])
	consume('marksep')
	tok = peek(0)
	#if tok[0] != 'block':
	if tok[0] == 'word':
		tok1 = peek(1)
		tok2 = peek(2)
		tok3 = peek(3)
		attr = None
		attstr = ''
		assg = ''
	
		if tok1[0] == 'dot' and tok2[0] == 'word':
			nexttok()
			nexttok()
		
			if tok[1] == 'xact':
				if tok2[1] != 'pr':
					try:
						getattr(interpreter, 'xact.params['+tok2[1]+']')
					except AttributeError:
						errors.print_error(25, lineindex, 
						[interpreter.xact.group, tok2[1]])
					attrstr = 'xact.params['+tok2[1]+']'
				else:
					attrstr = 'xact.pr'
			else:
				errors.print_error(26, lineindex, [tok[1]])
			
			# Always succeeds (because otherwise 
			# it will fail before this point).
			attr = getattr(interpreter, attrstr)
			assg = tok3[0]
		else:
			attrstr = ''
			if tok[1] in interpreter.ints:
				attrstr = 'ints['+tok[1]+']'
			elif tok[1] in interpreter.floats:
				attrstr = 'floats['+tok[1]+']'
			elif tok[1] in interpreter.strs:
				attrstr = 'strs['+tok[1]+']'
			else:
				errors.print_error(27, lineindex, [tok[1]])
			attr = getattr(interpreter, attrstr)
			assg = tok1[0]
		
		global assgs	
		
		if assg in assgs:
			if assg == 'inc':
				if type(attr) is str:
					errors.print_error(7, lineindex, ['inc'])
				attr += 1
			elif assg == 'dec':
				if type(attr) is str:
					errors.print_error(7, lineindex, ['dec'])
				attr -= 1
			else:
				nexttok()
				nexttok()
				result = parseExpression()
			   	if tok3[0] == 'eq':
			   		attr = result
			   	elif tok3[0] == 'add':
			   		attr += result
			   	elif tok3[0] == 'subt':
			   		attr -= result
			   	elif tok3[0] == 'multeq':
			   		attr *= result
			   	elif tok3[0] == 'diveq':
			   		attr /= result
			   	elif tok3[0] == 'pwreq':
			   		attr = attr ** result
			   	elif tok3[0] == 'remaineq':
			   		attr %= result
			   	return ('move', [])
		else:
			errors.print_error(21, lineindex, 
				   ['assignment operator or "."', tok], 'C')
	
	elif tok[0] == 'block':
		if tok[1] == 'inject':
			name = 'move'
		else:
			name = tok[1]
			nexttok()
			consume('lparen')
			while True:
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
	else:
		errors.print_error(21, lineindex, 
		       ['executive block or assignment lvalue', tok], 'E')

def parseInjector(line):
	newinj = None
	global tokline
	global pos
	pos = 0
	tokline = line
	global lineindex
	lineindex = interpreter.toklines.index(line)+1
	
	if peek(0)[0] == 'word':
		if peek(0)[1] in interpreter.marks:
			consume('word')
		else:
			errors.print_error(15, lineindex, [peek(0)[1]])
	consume('marksep')
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
		tok1 = nexttok()
		consume('eq')
		tok2 = nexttok()
		
		if tok1[1].startswith('p'):
			if tok2[0] != 'number' or tok2[1].index('.') != -1:
				errors.print_error(19, lineindex, ['integer', tok1[1], tok2[0]])
			else:
				params[tok1[1]] = int(tok2[1])
		elif tok1[1].startswith('f'):
			if tok2[0] != 'number':
				errors.print_error(19, lineindex, ['number', tok1[1], tok2[0]])
			else:
				params[tok1[1]] = float(tok2[1])
		elif tok1[1].startswith('str'):
			if tok2[0] != 'string':
				errors.print_error(19, lineindex, ['string', tok1[1], tok2[0]])
			else:
				params[tok1[1]] = tok2[1]
		else:
			print_warning(2, lineindex, [tok1[1]])
			params[tok1[1]] = tok2[1]
		
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
			if type(result1) is str and type(result) is not str:
				errors.print_error(20, lineindex)
			result += result1
			continue
		if matchtok('minus'):
			result1 = parseMult()
			if type(result1) is str or type(result) is str:
				errors.print_error(6, lineindex, ['-'])
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
				errors.print_error(6, lineindex, ['*'])
			result *= result1
			continue
		if matchtok('div'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				errors.print_error(6, lineindex, ['/'])
			result /= result1
			continue
		if matchtok('remain'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				errors.print_error(6, lineindex, ['%'])
			result = result % result1
			continue
		if matchtok('pwr'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				errors.print_error(6, lineindex, ['**'])
			result = result ** result1
			continue
		break
	
	return result
	
def parseUnary():
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
	
		if matchtok('dot'):
			tk = peek(0)
			if tk[1] in fac_params and tok[1] in interpreter.facilities:
				val = getattr(interpreter.facilities[tok[1]], tk[1])
				
			elif tk[1] in queue_params and tok[1] in interpreter.queues:
				val = getattr(interpreter.queues[tok[1]], tk[1])
			
			elif tok[1] == 'xact':
				if tk[1] not in xact_params:
					try:
						val = getattr(interpreter.xact, 'params['+tk[1]+']')
					except AttributeError:
						errors.print_error(25, lineindex, 
						       [interpreter.xact.group, tk[1]])
				else:
					val = getattr(interpreter.xact, tk[1])
			
			elif tk[1] == 'name':
				if tok[1] in interpreter.ints:
					val = interpreter.ints[tok[1]].name
				elif tok[1] in interpreter.floats:
					val = interpreter.floats[tok[1]].name
				elif tok[1] in interpreter.strs:
					val = interpreter.strs[tok[1]].name
				else:
					errors.print_error(28, lineindex, [tok[1]])
			else:
				errors.print_error(21, lineindex, 
				       ["name of parameter of defined variable", tok[1]], 'B')
				
			return val
		
		# If there is no dot:
		if tok[1] in interpreter.ints:
			val = interpreter.ints[tok[1]].value
		elif tok[1] in interpreter.floats:
			val = interpreter.floats[tok[1]].value
		elif tok[1] in interpreter.strs:
			val = interpreter.strs[tok[1]].value
		elif tok[1] in interpreter.facilities:
			val = interpreter.facilities[tok[1]].name
		elif tok[1] in interpreter.queues:
			val = interpreter.queues[tok[1]].name
		elif tok[1] in interpreter.marks:
			val = interpreter.marks[tok[1]].name
		else:
			errors.print_error(6, lineindex, tok)
	nexttok()
	
	return val

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
				       [toktype, peek(0)[0]], 'A')
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
