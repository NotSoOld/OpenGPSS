##################################################
#    ____                ________  ________      #
#   / __ \___  ___ ___  / ___/ _ \/ __/ __/      #
#  / /_/ / _ \/ -_) _ \/ (_ / ___/\ \_\ \        #
#  \____/ .__/\__/_//_/\___/_/  /___/___/        #
#      /_/           by NotSoOld, 2017 (c)       #
#                                                #
#         route|process|gather stats             #
#                                                #
# lexer.py - converts program text into tokens   #
# for parser                                     #
#                                                #
##################################################



import sys
import errors

tokens = []
numbers = '0123456789'
letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
operatorChars = '+-*/%=<>()|&!{};:,.[]?~'
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
             '?':'transport_if',
             '~':'indirect',
             '[[':'lmatrix',
             ']]':'rmatrix'
            }
             
typedefs = [
            'int', 
            'float', 
            'str',
            'bool',
            'fac', 
            'hist',
            'graph',
            'queue', 
            'mark',
            'chain',
            'function'
           ]

blocks = [
          'exitwhen',     # tested
          'inject',       # tested
          'reject',       # tested
          'fac_enter',    # tested
          'fac_leave',    # tested
          'fac_irrupt',   # implemented
          'fac_goaway',   # implemented
          'fac_avail',    # implemented
          'fac_unavail',  # implemented
          'queue_enter',  # tested
          'queue_leave',  # tested
          'wait',         # tested
          'transport',    # tested
          'transport_prob',#tested
          'transport_if', # tested
          'if',           # tested
          'else_if',      # tested
          'else',         # tested
          'wait_until',   # tested
          'chain_enter',  # tested
          'chain_leave',  # tested
          'chain_purge',  # tested
          'chain_pick',   # implemented
          'chain_find',   # implemented
          'while',        # tested
          'loop_times',   # tested
          'copy',         # tested
          'output',       # tested
          'xact_report',  # tested
          'review_cec',   # tested
          'move',         # tested
          'iter_next',    # tested
          'iter_stop',    # tested
          'interrupt',    # tested
          'flush_cec',    # tested
          'pause_by_user',# tested
          'hist_sample',  # tested
          'graph_sample'  # implemented
         ]
         
builtins = [
            'to_str',       # tested
            'to_int',       # tested
            'to_float',     # tested
            'to_bool',      # tested
            'random_int',   # tested
            'random_float', # tested
            'random01',     # tested
            'find',         # implemented
            'find_minmax',  # implemented
            'abs_value',    # tested
            'exp_distr',    # implemented
            'round_to'      # implemented
           ]

pos = 0
allprogram = []

def analyze(program):
	global pos
	global allprogram
	global tokens
	tokens = []
	pos = 0
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
