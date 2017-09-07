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
          'exitwhen',
          'inject',
          'reject',
          'fac_enter',
          'fac_leave',
          'fac_irrupt',
          'fac_goaway',
          'fac_avail',
          'fac_unavail',
          'queue_enter',
          'queue_leave',
          'wait',
          'transport',
          'transport_prob',
          'transport_if',
          'if',
          'else_if',
          'else',
          'wait_until',
          'chain_enter',
          'chain_leave',
          'chain_purge',
          'chain_pick',
          'chain_find',
          'while',
          'loop_times',
          'copy',
          'output',
          'xact_report',
          'review_cec',
          'move',
          'iter_next',
          'iter_stop',
          'interrupt',
          'flush_cec',
          'pause_by_user',
          'hist_sample',
          'graph_sample'
         ]
         
builtins = [
            'to_str',
            'to_int',
            'to_float',
            'to_bool',
            'random_int',
            'random_float',
            'random01',
            'find',
            'find_minmax',
            'abs_value',
            'exp_distr',
            'round_to'
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
		if cur == '\\' and peek(1) == '"':
			pass
		else:
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
