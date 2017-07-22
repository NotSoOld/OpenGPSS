##################################################
#    ____                ________  ________      #
#   / __ \___  ___ ___  / ___/ _ \/ __/ __/      #
#  / /_/ / _ \/ -_) _ \/ (_ / ___/\ \_\ \        #
#  \____/ .__/\__/_//_/\___/_/  /___/___/        #
#      /_/           by NotSoOld, 2017 (c)       #
#                                                #
#         route|process|gather stats             #
#                                                #
# OpenGPSS Interpreter.py - starts all action!   #
#                                                #
##################################################



from modules import interpreter, errors
import os
import config

config.load_config_file()
interpreter.print_logo()
print 'name of file with system to simulate:'
f = raw_input()
filepath = os.path.dirname(os.path.abspath(__file__))+'/'+f+'.ogps'
if not os.path.isfile(filepath):
	errors.print_error(1, '', [filepath])
interpreter.start_interpreter(filepath)
