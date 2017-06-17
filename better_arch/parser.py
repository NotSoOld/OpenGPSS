import sys


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

def parseDefinition(defline):
    pass

def parseBlock(blockline):
    pass

def parseExpression(expr):
    pass

def parseBinary(expr1, expr2):
    pass