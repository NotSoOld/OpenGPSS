# OpenGPSS Interpreter (beta v0.1)

## What's GPSS?
GPSS (General Purpose Simulation System) is a special programming language which is used for modelling different systems to get knowledge about their efficiency with selected parameters (so, some conclusions can be made: maybe, parameters should be changed, the system itself should be reorganized, etc.)

Systems which can be simulated in GPSS language should have following principles:
- there are *transacts* in the system which can either enter or leave the system and move through it.
- transacts do some actions while moving in the model; the most common actions (besides following different paths inside system) are staying in *queues*, processing in *facilities* and *waiting* while processing.

Examples of such systems: shops (one can move among shelves with food, then stay in queue, then process at the cashbox), computer systems (transacts are electric signals or information messages), public transport (people move from stop to stop)

## Why reinvent existing GPSS?
There already is properly working GPS language and pretty good interpreter. But this language is very old and has rather odd and ugly syntax along with silly restrictions. Also, it is a commercial project and there is no source code of GPS interpreter.

So, I try to recreate an idea of GPSS with C-like syntax, open source interpreter and (maybe?) more possibilities without restrictions. 

Btw, you may contribute your ideas, I'll go through all of them - we can make OpenGPSS better together!

## Usage:
`python OpenGPSS\ Interpreter.py`

## Manuals:
- [EN](./Manual.md) 
- RU: (will be someday)
