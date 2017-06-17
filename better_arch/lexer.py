import sys

tokens = []
numbers = '0123456789'
letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
operatorChars = '+-*/=<>()|&!{};:,.[]'
operators = {
             '+':'plus', 
             '-':'minus', 
             '*':'mult', 
             '/':'div', 
             '**':'pwr', 
             '=':'eq', 
             '+=':'add', 
             '-=':'subt',
             '*=':'multeq', 
             '/=':'diveq', 
             '**=':'pwreq', 
             ',':'comma',
             '.':'dot',
             '>':'gt', 
             '<':'less', 
             '>=':'gteq', 
             '<=':'lesseq', 
             '==':'compeq', 
             '||':'or', 
             '&&':'and', 
             '!':'not',
             '++':'inc', 
             '--':'dec', 
             '(':'lparen', 
             ')':'rparen',
             '{':'lbrace', 
             '}':'rbrace', 
             '[':'lbracket', 
             ']':'rbracket', 
             ';':'eocl', 
             ':':'marksep',
             '{{':'lexecblocks',
             '}}':'rexecblocks'
            }
             
typedefs = [
            'int', 
            'float', 
            'str', 
            'fac', 
            'fac_enum', 
            'queue', 
            'mark'
           ]

blocks = [
          'exitwhen',
          'inject',
          'reject',
          'fac_enter',
          'fac_leave',
          'queue_enter',
          'queue_leave',
          'wait',
          'if',
          'else_if',
          'else',
          'try',
          'chain_enter',
          'chain_leave',
          'travel',
          'travel_if',
          'while',
          'for'
         ]

pos = 0
allprogram = []


def analyze(program):
	global pos
	global allprogram
	allprogram = program
	
	while pos < len(allprogram):
		char = peek(0)
		if char == '"':
			tokenizeString()
		elif char in numbers:
			tokenizeNumber()
		elif char in letters+'_':
			tokenizeWord()
		elif char in operatorChars:
			tokenizeOperator()
		else:
			nextchar()
	return tokens

def addToken(tokenType, value=''):
	global tokens
	tokens.append([tokenType, value])

def tokenizeNumber():
	result = ''
	cur = peek(0)
	while True:
		if cur == '.':
			if '.' in result:
				print 'Incorrect float number!'
				sys.exit()
			result += cur
		elif cur in numbers:
			result += cur
		else:
			break
		cur = nextchar()
	addToken('number', result)

def tokenizeWord():
	cur = peek(0)
	buf = ''
	while True:
		if cur not in letters+numbers+'_':
			if buf in typedefs:
				addToken('typedef', buf)
			elif buf in blocks:
				addToken('block', buf)
			else:
				addToken('word', buf)
			return
		buf += cur
		cur = nextchar()

def tokenizeOperator():
	cur = peek(0)
	buf = ''
	
	if cur == '/' and peek(1) == '/':
		nextchar()
		nextchar()
		cur = peek(0)
		while True:
			if cur in '\n\r\0':
				nextchar()
				return
			cur = nextchar()
	if cur == '/' and peek(1) == '*':
		nextchar()
		nextchar()
		cur = peek(0)
		while True:
			if cur == '*' and peek(1) == '/':
				nextchar()
				nextchar()
				return
			cur = nextchar()
				
	while True:
		if buf and buf+cur not in operators:
			addToken(operators[buf])
			return
		buf += cur
		cur = nextchar()
		
def tokenizeString():
	nextchar()
	cur = peek(0)
	buf = ''
	while True:
		if cur == '"':
			addToken('string', buf)
			nextchar()
			return
		buf += cur
		cur = nextchar()

def peek(relpos):
	global pos
	cur = pos + relpos
	if cur >= len(allprogram):
		return ''
	return allprogram[cur]

def nextchar():
	global pos
	pos += 1
	return peek(0)
