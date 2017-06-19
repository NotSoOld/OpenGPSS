import sys

pos = 0

def tocodelines(program):
    parsed = []
    i = 0
    while i < len(program):
        token = program[i]
        if token[0] in 'lbrace'+'rbrace'+'lexecblocks'+'rexecblocks':
            parsed.append([token])
            i += 1
            continue

        line = []
        while True:
            token = program[i]
            if token[0] == 'eocl':
                parsed.append(line)
                i += 1
                break
            line.append(token)
            i += 1
            if i >= len(program):
                print 'Unexpected end of program during parsing lines'
                sys.exit()
    return parsed

def parseDefinition(line):
    pos = 0
    name = ''
    newobj = None
    deftype = line[0][1]
    
    if deftype == 'int':
        pass
    elif deftype == 'float':
        pass
    elif deftype == 'fac':
        pass
    elif deftype == 'queue':
        pass
    elif deftype == 'chain':
        pass
    elif deftype == 'block':
        pass
    elif deftype == 'str':
        pass
    else: # If deftype is fac_enum
        pass
    
    #getattr(interpreter, deftype+'s')[name] = newobj

def parseBlock(line):
    pass

def parseExpression(expr):
    pass

def parseBinary(expr1, expr2):
    pass

#os.path.dirname(os.path.abspath(__file__))