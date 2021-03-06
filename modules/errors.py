##################################################
#    ____                ________  ________      #
#   / __ \___  ___ ___  / ___/ _ \/ __/ __/      #
#  / /_/ / _ \/ -_) _ \/ (_ / ___/\ \_\ \        #
#  \____/ .__/\__/_//_/\___/_/  /___/___/        #
#      /_/           by NotSoOld, 2017 (c)       #
#                                                #
#         route|process|gather stats             #
#                                                #
# errors.py - error and warning handler, prints  #
# messages to console                            #
#                                                #
##################################################



import sys
import interpreter

errors = {
          1:'No such file: "{}"',
          2:'Unexpected end of file during parsing program into lines',
          3:'Name of the definition expected; got "{}" "{}"',
          4:'Unknown parameter "{}" or missing "}}" during initialization',
          5:'Expected initial value of type "{}" for parameter "{}"; got "{}"',
          6:'Expected name of defined variable/structure/array or value; '\
            'got "{}"',
          7:'Cannot {}rement string or boolean',
          8:'Cannot apply operation "{}" for string values',
          9:'Found incorrect float number "{}" during analysis',
          10:'Initial value for integer variable "{}" must be of type "int"',
          11:'Initial value for float variable "{}" must be a number',
          12:'Nothing or "{}" expected; got "{}"',
          13:'Mark "{}" found more than once as transporting label ' \
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
          26:'Unknown structure value "{}" (are you trying to assign to ' \
             'read-only parameters?)',
          27:'Unknown variable: "{}"',
          28:'Cannot take name of "{}", because it is unknown',
          29:'Error while transporting: undefined mark "{}"',
          30:'Mark "{}" is not present anywhere as transporting label '\
             '(at the left of ":")',
          31:'Cannot convert "{}" into "{}"',
          32:'Initial value for boolean variable "{}" must be true/false word',
          33:'Cannot perform "{}" for types "{}" and "{}".\nYou can use '\
             'builtin functions to convert types.',
          34:'What type of transport is there? Expected ">", "|" or "?", got "{}"',
          35:'Condition or probability argument is missing',
          36:'"}}" for "if"/"else_if"/"else" block is missing',
          37:'"}}" for "while"/"loop_times" block is missing',
          38:'Cannot find the "owner" (block) of "{}" in line "{}"',
          39:'Xact is trying to enter queue which it already entered',
          40:'Xact is trying to leave queue which it did not enter',
          41:'Xact is trying to occupy facility which it already occupies',
          42:'Xact is trying to leave facility which it did not occupy',
          43:'No such facility: {}',
          44:'No such queue: {}',
          45:'Expected ","; got end of line during parsing "loop_times" block',
          46:'Cannot do assignment; "{}" is a read-only value',
          47:'Xact is trying to interrupt facility which it already occupies',
          48:'No such chain: "{}"',
          49:'Unknown search criteria for "find/find_minmax" function: "{}"',
          50:'Unknown parameter "{}", cannot execute search for it',
          51:'Expected parameters for histogram initialization',
          52:'Some parameters for histogram initialization are missing ' \
             '(must be "start", "interval" and "count")',
          53:'No such histogram: "{}"',
          54:'Wrong function definition (expecting one condition per each ' \
             'return expression; got "{}" expressions when expected "{}")',
          55:'Wrong number of arguments for function "{}" (takes "{}", "{}" given)',
          56:'Array index "{}" is out of range "({}, {})"',
          57:'Cannot find attachable module "{}" (it must be in the same '\
             'folder where .ogps file is)',
          58:'Attachable module "{}" does not have function "{}"',
          59:'No such graph: "{}"',
          60:'Unknown configuration parameter: "{}"',
          61:'Multiple variable/array definition with the same name "{}"',
          62:'Arrays/matrices of type "{}" are not allowed',
          63:'Value of parameter {} is of unknown type'
         }

warnings = {
            1:'Everything except definitions in non-executive area will be '\
              'totally IGNORED.\nIf you see this, double-check definition '\
              'area of your program.',
            3:'Mark "{}" cannot be found as transporting label (at the left of '\
              '":"). Is it needed at all?',
            4:'Duplicate xact parameter "{}"; previous value of "{}" '\
              'will be OVERWRITTEN.',
            5:'Attachable module "{}" is either already imported or its name '\
              'conflicts with one of other attachable modules. Double-check '\
              '"attach" statements in your program.'
           }

def print_error(error_code, line, args=[], add=''):
	
	if interpreter.original_stdout:
		sys.stdout = interpreter.original_stdout
	
	print '\n\n'+'/'*30
	print 'ERROR {!s}{!s} in line {!s}:'.format(error_code, add, line)
	print errors[error_code].format(*args)
	print '\n'
	if interpreter.original_stdout:
		sys.stdout = interpreter.original_stdout
		print 'An error occured, see logs for futher information.\n'
	sys.exit()
	
def print_warning(warn_code, line, args=[]):
	if interpreter.original_stdout:
		sys.stdout = interpreter.original_stdout
	print '\n\n'+'/'*30
	print 'WARNING {!s} in line {!s}:'.format(warn_code, line)
	print warnings[warn_code].format(*args)
	print '\n'
	if interpreter.logfile:
		sys.stdout = interpreter.logfile
