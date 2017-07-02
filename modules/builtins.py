import errors
import random
import parser

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
