import sys
import tree


# Error handler
class Error_handler:
    def __init__(self):
        self.type = None
        self.node = None
        self.types = ['UnexpectedError',
                      'NoInputPoint',
                      'RedeclarationError',
                      'UndeclaredError',
                      'FuncCallError',
                      'ConverseError',
                      'ValueError',
                      'WrongParameters',
                      'Recursion',
                      'TypeError']

    def call(self, err_type, node=None):
        self.type = err_type
        self.node = node
        sys.stderr.write(f'Error {self.types[int(err_type)]}: ')
        if self.type == 0:
            sys.stderr.write(f' incorrect syntax at '
                                 f'{self.node.child[0].lineno} line: {self.node.child[0].value} \n')
            return
        if self.type == 1:
            sys.stderr.write(f'no program detected\n')
            return
        elif self.type == 2:
            if node.type == 'assignment':
                sys.stderr.write(f'variable "{self.node.child[0].value}" at '
                                 f'{self.node.child[0].lineno} line is already declared\n')
            else:
                sys.stderr.write(f'variable "{self.node.value}" at '
                                 f' {self.node.lineno} line is already declared\n')
        elif self.type == 3:
            if node.type == 'assignment':
                sys.stderr.write(f'variable "{self.node.child[0].value}" at '
                                 f'{self.node.child[0].lineno} line is used before declaration\n')
            else:
                sys.stderr.write(f'variable "{self.node.value}" at '
                                 f' {self.node.lineno} line is used before declaration\n')
        elif self.type == 4:
            sys.stderr.write(f'Unknown procedure call "{self.node.value}" at '
                             f' {self.node.lineno} line\n')
        elif self.type == 5:
            if node.type == 'assignment':
                sys.stderr.write(f'wrong type variable "{self.node.child[0].value}" at '
                                 f'{self.node.child[0].lineno} line\n')
            else:
                sys.stderr.write(f'failed to converse variable "{self.node.value}" at '
                                 f' {self.node.child[0].lineno} line\n')
        elif self.type == 6:
            if node.type == 'assignment':
                sys.stderr.write(f'incompatible value and type: "{self.node.child[0].value}" at'
                                 f' {self.node.child[0].lineno} line\n')
            else:
                sys.stderr.write(f'unexpected value type: "{self.node.value}" at'
                                 f' {self.node.child[0].lineno}  line\n')
        elif self.type == 7:
            if node.type == 'assignment':
                sys.stderr.write(f'tried to call procedure with wrong parameters: "{self.node.child[0].value}" at'
                                 f' {self.node.child[0].lineno} line\n')
            else:
                sys.stderr.write(f'tried to call procedure with wrong parameters: "{self.node.value}" at'
                                 f' {self.node.lineno} line\n')
        elif self.type == 8:
            if node.type == 'assignment':
                sys.stderr.write(f'procedure calls itself too many times: "{self.node.child[0].value}" at'
                                 f' {self.node.child[0].lineno} line\n')
            else:
                sys.stderr.write(f'procedure calls itself too many times: "{self.node.value}" at'
                                 f'  {self.node.child[0].lineno} line\n')
        elif self.type == 9:
            if node.type == 'assignment':
                sys.stderr.write(f'type error: "{self.node.child[0].value}" at'
                                 f' {self.node.child[0].lineno} line\n')
            else:
                sys.stderr.write(f'type error: "{self.node.value}" at'
                                 f' {self.node.child[0].lineno}  line\n')


class InterpreterNameError(Exception):
    pass


class InterpreterIndexError(Exception):
    pass


class InterpreterRedeclarationError(Exception):
    pass


class InterpreterConverseError(Exception):
    pass


class InterpreterValueError(Exception):
    pass


class InterpreterRecursion(Exception):
    pass