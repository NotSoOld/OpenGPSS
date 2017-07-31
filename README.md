```
     ____                ________  ________
    / __ \___  ___ ___  / ___/ _ \/ __/ __/
   / /_/ / _ \/ -_) _ \/ (_ / ___/\ \_\ \
   \____/ .__/\__/_//_/\___/_/  /___/___/
       /_/           by NotSoOld, 2017 (c)
   
          route|process|gather stats
          
```

---

# OpenGPSS Interpreter (beta v0.3)

*([README на русском](./README_RU.md))*

## What's GPSS?
GPSS (General Purpose Simulation System) is a special programming language which is used for modelling different systems to get knowledge about their efficiency with selected parameters (so, some conclusions can be made: maybe, parameters should be changed, the system itself should be reorganized, etc.)

Systems which can be simulated in GPSS language should have following principles:
- there are *transacts* (or *xacts*) in the system which can either enter or leave the system and move through it.
- transacts do some actions while moving in the model; the most common actions (besides following different paths inside system) are staying in *queues*, processing in *facilities* and *waiting* while processing.

Examples of such systems: shops (one can move among shelves with food, then stay in queue, then process at the cashbox), computer systems (transacts are electric signals or information messages), public transport (people move from stop to stop)

## Why reinvent existing GPSS?
There already is properly working GPS language and pretty good interpreter. But this language is very old and has rather odd and ugly syntax along with silly restrictions. Also, it is a commercial project and there is no source code of GPS interpreter.

So, I try to recreate an idea of GPSS with C-like syntax, open source interpreter and more possibilities and less restrictions. 

Feel free to contribute your ideas, I'll go through all of them - we can make OpenGPSS better together!


## Advantages over old GPSS:

- common, user-friendly syntax (instead of GPSS "Assembly-like" ugly and odd syntax), for example:

	\- required definition area (you will never forget what variables and structures you are using in your model)
	
	\- possible to use expressions in arguments and parameters (no more strange VARIABLE constructions and other limitations due to GPSS's age), no more weird rules like limited length of variable names, etc.
	
	\- extended support of conditional functions and functions in Python modules (forget about these FUNCTION blocks where you need to tabulate each math function)
	
	\- common branching and cycling operators
	
	\- define exit condition exactly as you need (no more START/END blocks and TERMINATE with counter)
	
	\- variables instead of savevalues and logic gates, one undestandable block instead of TEST and GATE
	
	\- PRIORITY and ASSIGN and group names (which were the fist thing you will always forget about) are replaced by common "." operator
	
	\- lots of debugging possibilities, understandable error messages

- brand new possibilities (find them all by yourselves) and improved old possibilites for modelling

- open-source interpreter, creator support and comprehensive manual in two languages


## Usage:

1. Install Python 2.7 (or newer version of Python 2.x) package or IDE or interpreter

2. Run in terminal from root folder:

`python OpenGPSS\ Interpreter.py`

or start Python IDE/interpreter/etc. and run *OpenGPSS Interpreter.py*

## Manuals:
- [EN](./manuals/Manual.md) 
- [RU](./manuals/Manual_RU.md)
