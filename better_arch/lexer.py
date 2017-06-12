import sys

tokens = []
numbers = '0123456789'
letters = 'abcdefghijklmnopqrstuvwxyz'
operators = '+-*/'
pos = 0

def addToken(tokenType, value):
    global tokens
    tokens.append([tokenType, value])

def tokenizeNumber():
    result = ''
    cur = peek(0)
    while True:
        if cur == '.':
            if '.' in result:
                print 'Incorrect float number!'
                sys.exit()
            result += cur
        elif cur in numbers:
            result += cur
        else:
            break
        cur = nextchar()
    addToken('number', result)

def tokenizeWord():
    pass

def tokenizeOperator():
    pass

def peek(relpos):
    global pos
    cur = pos + relpos
    if cur >= len(allprogram):
        return ''
    return allprogram[cur]

def nextchar():
    global pos
    pos += 1
    return peek(0)

progfile = open('prog1.ogps', 'r')
allprogram = progfile.read()
progfile.close()
char = peek(0)
while pos < len(allprogram):
    if char in numbers:
        tokenizeNumber()
    elif char in letters:
        tokenizeWord()
    elif char in operators:
        tokenizeOperator()
    char = nextchar()

print tokens