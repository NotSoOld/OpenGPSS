import errors
import random
import parser
import interpreter
import copy

def random01():
	random.seed()
	return random.random()
	
def random_int(l, r):
	random.seed()
	return random.randint(l, r)
	
def random_float(l, r):
	random.seed()
	return random.uniform(l, r)
	
def to_str(val):
	return str(val)
	
def to_bool(val):
	if (type(val) is not int or type(val) is not float
	    or type(val) is not bool) and val != 'true' and val != 'false':
		errors.print_error(31, parser.lineindex, [val, 'bool'])
	if val == 'true':
		return True
	if val == 'false':
		return False
	if val != 0:
		return True
	return False
	
def to_int(val):
	ret = 0
	try:
		ret = int(val)
	except ValueError:
		errors.print_error(31, parser.lineindex, [val, 'int'])
	return ret
	
def to_float(val):
	ret = 0
	try:
		ret = float(val)
	except ValueError:
		errors.print_error(31, parser.lineindex, [val, 'float'])
	return ret
	
def find(line):
	# find(facilities.curplaces > 0) ==> name of facility
	# find(chains.length < 10) ==> name of chain
	# find(chains.xacts.p2 == 5) ==> xact index
	i = 0
	parserline = copy.deepcopy(parser.tokline)
	oldpos = parser.pos
	
	if line[0][1] == 'facilities' or line[0][1] == 'queues' or \
	   line[0][1] == 'chains':
	   	attr = getattr(interpreter, line[0][1])
	   	if line[0][1] == 'chains' and line[2][1] == 'xacts':
	   		buf = getattr(attr, line[2][1])
	   		for xa in buf:
	   			xa_attr = None
	   			try:
	   				xa_attr = getattr(xa, line[4][1])
	   			except AttributeError:
	   				errors.print_error(50, parser.lineindex, [line[4][1]])
	   			nl = [['number', xa_attr]] + line[5:]
				parser.tokline = nl
				parser.pos = 0
				if parser.parseExpression():
					parser.tokline = copy.deepcopy(parserline)
					parser.pos = oldpos
					return xa.index
	   			
	   	for item in attr.keys():
	   		val = 0
	   		try:
	   			val = getattr(attr, line[2][1])
	   		except AttributeError:
	   			errors.print_error(50, parser.lineindex, [line[2][1]])
	   		nl = [['number', val]] + line[3:]
			parser.tokline = nl
			parser.pos = 0
			if parser.parseExpression():
				parser.tokline = copy.deepcopy(parserline)
				parser.pos = oldpos
				return '~'+item
		return -1
	else:
		errors.print_error(49, parser.lineindex, [line[0][1]+'.'+line[2][1]])
