from modules import interpreter, errors
import os
import config

config.load_config_file()
print '<<welcome message>>'
print 'name of file with system to simulate:'
f = raw_input()
filepath = os.path.dirname(os.path.abspath(__file__))+'/'+f+'.ogps'
if not os.path.isfile(filepath):
	errors.print_error(1, '', [filepath])
interpreter.start_interpreter(filepath)
