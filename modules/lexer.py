import sys
import errors

tokens = []
numbers = '0123456789'
letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
operatorChars = '+-*/%=<>()|&!{};:,.[]?'
operators = {
             '+':'plus', 
             '-':'minus', 
             '*':'mult', 
             '/':'div', 
             '%':'remain',
             '**':'pwr', 
             '=':'eq', 
             '+=':'add', 
             '-=':'subt',
             '*=':'multeq', 
             '/=':'diveq', 
             '**=':'pwreq', 
             '%=':'remaineq',
             ',':'comma',
             '.':'dot',
             '>':'gt', 
             '<':'less', 
             '>=':'gteq', 
             '<=':'lesseq', 
             '==':'compeq', 
             '!=':'noteq',
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
             '{{':'lexec',
             '}}':'rexec',
             '->':'transport',
             '|':'transport_prob',
             '?':'transport_if'
             #'~':'indirect_addr'
            }
             
typedefs = [
            'int', 
            'float', 
            'str',
            'bool',
            'fac', 
            #'gist',
            'queue', 
            'mark',
            'chain'
            #'sub'
           ]

blocks = [
          'exitwhen',     # tested
          'inject',       # tested
          'reject',       # tested
          'fac_enter',    # tested
          'fac_leave',    # tested
          #'fac_force',
          #'fac_goaway',
          'queue_enter',  # tested
          'queue_leave',  # tested
          'wait',         # tested
          'if',           # tested
          'else_if',      # tested
          'else',         # tested
          'try',          # tested
          'chain_enter',  # tested
          'chain_leave',  # tested
          'chain_purge',  # tested
          #'chain_leaveif',
          #'find',
          #'find_minmax',
          'while',        # tested
          #'loop_times',
          'copy',         # tested
          'output',       # tested
          'xact_report',  # tested
          'review_cec',   # tested
          'move',         # tested
          'iter_next',    # --broken
          'iter_stop',    # --broken
          'interrupt',    # tested
          'flush_cec'     # tested
          #'pause_by_user'
          #'system_info'
         ]
         
builtins = [
            'to_str',
            'to_int',
            'to_float',
            'to_bool',
            'random_int',
            'random_float',
            'random01'
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
				errors.print_error(9, '', [result+'.'])
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
			elif buf in builtins:
				addToken('builtin', buf)
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
