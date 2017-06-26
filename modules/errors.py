import sys

errors = {
          1:'No such file: "{}"',
          2:'Unexpected end of file during parsing program into lines',
          3:'Name of the definition expected; got "{}" "{}"',
          4:'Unknown facility parameter "{}" or missing "{{"',
          5:'Expected parameter of type "{}" for facility parameter '\
          '"{}"; got "{}"',
          6:'Expected name of defined variable or value; got "{} {}"',
          7:'Cannot {}rement string',
          8:'Cannot apply operation "{}" for string values',
          9:'Found incorrect float number "{}" during analysis',
          10:'Initial value for integer variable "{}" must be of type "int"',
          11:'Initial value for float variable "{}" must be a number',
          12:'Nothing or "{{" expected; got "{}"',
          13:'Mark "{}" found more than one time as travelling label ' \
          '(at the left of ":")',
          14:'Xact is trying to leave executive area',
          15:'Unknown word "{}" used as mark name',
          16:'"," or ")" expected while parsing arguments; got "{}"',
          17:'String "xact group name" expected; got "{}"',
          18:'Number argument expected; got "{}"',
          19:'Expected "{}" value for parameter "{}"; got "{}"',
          20:'Cannot do addition between string and non-string value',
          21:'"{}" expected; got "{}"',
          22:'Multiple definition of name "{}" with type "{}"',
          23:'Exit condition must be declared only once',
          24:'Index of executive line is out of bounds (probably missing "}}}}")',
          25:'Current xact from group "{}" does not have a parameter "{}"',
          26:'Unknown complex value "{}" (are you trying to assign to ' \
          'read-only parameters?)',
          27:'Unknown variable "{}"',
          28:'Cannot take name of "{}", because it is unknown'
         }

warnings = {
            1:'Everything except definitions in non-executive area will be '\
            'totally IGNORED.\nIf you see this, double-check definition '\
            'area of your program.',
            2:'Xact parameters\' custom names (like "{}") are acceptible but '\
            'HIGHLY undesirable because they can lead to "parameter not found"'\
            ' errors very easily (for example, for xacts from other group). '\
            'They also got type "string" by default which you may not want.' 
           }

def print_error(error_code, line, args=[], add=''):
	print 'ERROR {!s}{!s} in line {!s}:'.format(error_code, add, line)
	print errors[error_code].format(*args)
	sys.exit()
	
def print_warning(warn_code, line, args=[]):
	print 'WARNING {!s} in line {!s}:'.format(warn_code, line)
	print warnings[warn_code].format(*args)
