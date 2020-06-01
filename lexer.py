import ply.lex as lex
import sys


reserved = {
    'TRUE': 'TRUE',
    'FALSE': 'FALSE',
    'INT': 'INT',
    'BOOLEAN': 'BOOLEAN',
    'CINT': 'CINT',
    'CBOOLEAN': 'CBOOLEAN',
    'MAP': 'MAP',
    'INC': 'INC',
    'DEC': 'DEC',
    'NOT': 'NOT',
    'GT': 'GT',
    'LT': 'LT',
    'OR': 'OR',
    'WHILE': 'WHILE',
    'DO': 'DO',
    'IF': 'IF',
    'ELSE': 'ELSE',
    'PROC': 'PROC',

    'STEP': 'STEP',
    'BACK': 'BACK',
    'RIGHT': 'RIGHT',
    'LEFT': 'LEFT',
    'LOOK': 'LOOK',
    'BAR': 'BAR',
    'EMP': 'EMP',
    'SET': 'SET',
    'RESET': 'RESET',
    'CLR': 'CLR',
}


class lexer(object):

    def __init__(self):
        self.lexer = lex.lex(module=self)

    tokens = [
        'NAME', 'NUMBER', 'EQUALS', 'LPAREN', 'RPAREN', 'INCORRECT', 'NEWLINE', 'LBR', 'RBR'
    ]

    tokens += reserved.values()

    precedence = (
        ('right', 'INC', 'DEC'),
        ('right', 'ELSE', 'LPAREN'),
        ('left', 'RPAREN')
    )

    t_EQUALS = r'\:\='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBR = r'\['
    t_RBR = r'\]'

    t_ignore = " \t"

    @staticmethod
    def t_NUMBER(t):
        r'[\+-]?\d+'
        t.value = int(t.value)
        return t

    @staticmethod
    def t_NAME(t):
        r'[a-zA-Z][a-zA-Z0-9]*'
        t.type = reserved.get(t.value, 'NAME')
        return t

    @staticmethod
    def t_NEWLINE(t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")
        return t

    @staticmethod
    def t_INCORRECT(t):
        r'[^(a-zA-Z0-9\:\=\)\()\+-\[\]]'
        sys.stderr.write(f'>>> incorrect symbol "{t.value}" at {t.lexer.lineno} line \n')

    @staticmethod
    def t_error(t):
        # print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def input(self, _data):
        return self.lexer.input(_data)

    def token(self):
        return self.lexer.token()





if __name__ == '__main__':
    f = open('C:/Users/user/PycharmProjects/lab2/factorial.txt')
    data = f.read()
    f.close()
    lexer = lexer()
    lexer.input(data)
    while True:
        token = lexer.token()
        if token is None:
            break
        else:
            print(token)