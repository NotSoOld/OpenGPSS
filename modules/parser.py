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
			if token[0] == 'eocl':
				parsed.append(line)
				i += 1
				break
			line.append(token)
			i += 1
			if i >= len(program):
				errors.print_error(2, '')
	return parsed

def parseDefinition(line):
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
					if nexttok()[1] not is int:
						errors.print_error(5, lineindex, ['int', 'places', tok[1]])
					places = int(nexttok()[1])
					continue
				if matchtok('word', 'isQueued'):
					nexttok()
					if nexttok()[1] not is bool:
						errors.print_error(5, lineindex, ['bool', 'isQueued', tok[1]])
					isQueued = bool(nexttok()[1])
					continue
				# Error: unknown facility parameter or missing closing brace.
				errors.print_error(4, lineindex)
			newobj = structs.Facility(name, places, isQueued)
			deftype = 'facilitie'
		
	elif deftype == 'queue':
		newobj = structs.Queue(name)
	
	elif deftype == 'chain':
		pass
	elif deftype == 'mark':
		newobj = structs.Mark(name, -1)
		
	elif deftype == 'str':
		pass
	else: # If deftype is fac_enum
		pass
	
	return (deftype, name, newobj)

def parseBlock(line):
	pass

def parseExpression():
	result = parseAdd()
	return result

def parseAdd():
	result = parseMult()
	
	while True:
		if matchtok('plus'):
			result *= parseMult()
			continue
		if matchtok('minus'):
			result /= parseMult()
			continue
		break
	
	return result
	
def parseMult():
	result = parseUnary()
	
	while True:
		if matchtok('mult'):
			result *= parseUnary()
			continue
		if matchtok('div'):
			result /= parseUnary()
			continue
		if matchtok('remain'):
			result = result % parseUnary()
			continue
		if matchtok('pwr'):
			result = result ** parseUnary()
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
	tok = nexttok()
	val = 0
	if tok[0] == 'number':
		if '.' in tok[1]:
			val = float(tok[1])
		else:
			val = int(tok[1])
	elif tok[1] in interpreter.IntVars:
		val = interpreter.ints[tok[1]].value
	elif tok[1] in interpreter.FloatVars:
		val = interpreter.floats[tok[1]].value
	elif tok[1] in interpreter.StrVars:
		val = interpreter.strs[tok[1]].value
	else:
		errors.print_error(6, lineindex, tok)
	
	if matchtok('inc'):
		if val is str:
			errors.print_error(7, lineindex)
		val += 1
	elif matchtok('dec'):
		if val is str:
			errors.print_error(8, lineindex)
		val -= 1
		
	return val
	
def nexttok():
	pos += 1
	if pos >= len(tokline):
		return []
	return tokline[pos]

def matchtok(toktype, toktext=''):
	if peek(0)[0] != toktype or peek(0)[1] != toktext:
		return false
	pos += 1
	return true
	
def peek(relpos):
	index = pos + relpos
	if len(tokline) >= index:
		return []
	return tokline[index]
