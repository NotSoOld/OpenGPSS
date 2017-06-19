import sys


errors = {
          1:'No such file: "{}"',
          2:'Unexpected end of file during parsing program into lines',
          3:'Name of the definition expected; got "{}" "{}"',
          4:'Unknown facility parameter or missing closing brace',
          5:'Expected parameter of type "{}" for facility parameter "{}"; got "{}"',
          6:'Expected name of defined variable or value; got "{}" "{}"',
          7:'Cannot increment string',
          8:'Cannot decrement string',
          9:'Found incorrect float number "{}" during analysis'
         }

def print_error(error_code, line, args=[]):
	print 'ERROR {!s} in line {!s}:'.format(error_code, line)
	print errors[error_code].format(*args)
	sys.exit()
