import sys
import structs
import interpreter
import errors

pos = 0
tokline = []
lineindex = 0

def tocodelines(program):
	parsed = []
	i = 0
	while i < len(program):
		token = program[i]
		if token[0] in 'lbrace'+'rbrace'+'lexecblocks'+'rexecblocks':
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
	lineindex = interpreter.toklines.indexof(line)+1
	
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
					nexttok()
					if type(nexttok()[1]) is not int:
						errors.print_error(5, lineindex, ['int', 'places', tok[1]])
					places = int(nexttok()[1])
					continue
				if matchtok('word', 'isQueued'):
					nexttok()
					if type(nexttok()[1]) is not bool:
						errors.print_error(5, lineindex, ['bool', 'isQueued', tok[1]])
					isQueued = bool(nexttok()[1])
					continue
				# Error: unknown facility parameter or missing closing brace.
				errors.print_error(4, lineindex)
			newobj = structs.Facility(name, places, isQueued)
			deftype = 'facilitie'
		else:
			pass #error: nothing or '{' expected
		
	elif deftype == 'queue':
		newobj = structs.Queue(name)
	
	elif deftype == 'chain':
		pass
	elif deftype == 'mark':
		newobj = structs.Mark(name, -1)
		for line in interpreter.toklines:
			if line[0] == ['word', name] and line[1][0] == 'marksep':
				if newobj.block != -1:
					pass #error: mark 'name' found more than one time as travelling label (at the left of ':')
				newobj.block = interpreter.toklines.indexof(line)
			
		
	elif deftype == 'str':
		pass
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
	
	if tokline.indexof(['rexecblocks', '']) != -1:
		pass #error: xact is trying to leave executive area
	if peek(0)[0] == 'word':
		if peek(0)[1] in interpreter.marks:
			consume('word')
		else:
			pass #error: unknown word 'peek(0)[1] used as mark name'
	consume('marksep')
	tok = peek(0)
	if tok[0] != 'block':
		pass #error: expected executive block; got 'tok'
	if tok[1] == 'inject':
		name = 'move'
	else:
		name = tok[1]
		consume('lparen')
		while True:
			if peek(0)[0] == 'comma':
				consume('comma')
				continue
			elif peek(0)[0] == 'rparen':
				consume('rparen')
				break;
			else:
				pass #error: ',' or ')' expected while parsing arguments; got 'peek(0)'
			args.append(parseExpression())
	return (name, args)

def parseInjector(line):
	newinj = None
	global tokline
	global pos
	pos = 0
	tokline = line
	if peek(0)[0] == 'word' and peek(0)[1] in interpreter.marks:
		consume('word')
	else:
		pass #error: unknown word 'peek(0)[1] used as mark name'
	consume('marksep')
	consume('block', 'inject')
	consume('lparen')
	
	tok = peek(0)
	if tok[0] != 'str':
		pass #error: string 'group' expected
	group = tok[1]
	consume('comma')
	args = []
	for i in range (0, 4):
		tok = nexttok()
		if tok[0] != 'number':
			pass #error: number expected
		args.append(int(tok[1]))
		if i != 3:
			consume('comma')
		else:
			consume('rparen')
			
	blk = interpreter.indexof(line)
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
			if tok2[0] != 'number' or tok2[1].indexof('.') != -1:
					pass #error: expected integer value for parameter 'tok1[1]'
			else:
				params[tok1[1]] = int(tok2[1])
		elif tok1[1].startswith('f'):
			if tok2[0] != 'number':
					pass #error: expected number value for parameter 'tok1[1]'
			else:
				params[tok1[1]] = float(tok2[1])
		elif tok1[1].startswith('str'):
			if tok2[0] != 'string':
					pass #error: expected string value for parameter 'tok1[1]'
			else:
				params[tok1[1]] = int(tok2[1])
		
	newinj = structs.Injector(group, args[0], args[1], args[2], args[3], blk, params)
	return newinj
	
def parseExitCondition(line):
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
				pass #error: cannot do addition between string and non-string values
			result += result1
			continue
		if matchtok('minus'):
			result1 = parseMult()
			if type(result1) is str or type(result) is str:
				pass #error: cannot apply subtraction to string values
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
				pass #error: cannot apply multiplication to string values
			result *= result1
			continue
		if matchtok('div'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				pass #error: cannot apply division to string values
			result /= result1
			continue
		if matchtok('remain'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				pass #error: cannot apply remainder operation to string values
			result = result % result1
			continue
		if matchtok('pwr'):
			result1 = parseUnary()
			if type(result1) is str or type(result) is str:
				pass #error: cannot apply power operation to string values
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
	
	if matchtok('inc'):
		if type(val) is str:
			errors.print_error(7, lineindex)
		val += 1
	elif matchtok('dec'):
		if val is str:
			errors.print_error(8, lineindex)
		val -= 1
		
	return val

def consume(toktype, toktext=''):
	global pos
	if peek(0)[0] != toktype or peek(0)[1] != toktext:
		pass #error: 'toktype' expected, got 'peek(0)[0]'
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
