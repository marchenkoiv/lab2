import ply.yacc as yacc
from ply.lex import LexError
import sys
from typing import Dict

from lexer import lexer
from tree import node


class parser(object):
    tokens = lexer.tokens
    precedence = lexer.precedence

    def __init__(self):
        self.ok = True
        self.lexer = lexer()
        self.parser = yacc.yacc(module=self)
        self._functions: Dict[str, node] = dict()

    def parse(self, s):
        try:
            res = self.parser.parse(s)
            return res, self._functions, self.ok
        except LexError:
            sys.stderr.write(f'Illegal token {s}\n')

    @staticmethod
    def p_program(p):
        """program : statements"""
        p[0] = node('program', ch=p[1])

    @staticmethod
    def p_statements_group(p):
        """statements_group : LPAREN statements inner_statement RPAREN
                            | inner_statement"""
        if len(p) == 5:
            p[0] = node('group', ch=[p[2], p[3]])
        else:
            p[0] = p[1]

    @staticmethod
    def p_inner_statement(p):
        """inner_statement : declaration
                     | assignment
                     | while
                     | if
                     | command
                     | procedure
                     | call
                     | empty
                     | cell_proc
                     | arithmetic_expression"""

        p[0] = p[1]

    @staticmethod
    def p_statements(p):
        """statements : statements statement
                      | statement"""
        if len(p) == 2:
            p[0] = node('statements', ch=[p[1]])
        else:
            p[0] = node('statements', ch=[p[1], p[2]])

    @staticmethod
    def p_statement(p):
        """statement : declaration NEWLINE
                     | assignment NEWLINE
                     | while NEWLINE
                     | if NEWLINE
                     | command NEWLINE
                     | procedure NEWLINE
                     | call NEWLINE
                     | empty NEWLINE
                     | cell_proc NEWLINE
                     | arithmetic_expression NEWLINE"""
        p[0] = p[1]



    @staticmethod
    def p_declaration(p):
        """declaration : type name"""
        p[0] = node('declaration', val=p[1], ch=p[2])

    @staticmethod
    def p_declaration_error(p):
        """declaration : type error"""
        p[0] = node('declaration', val=p[1], ch=p[2])
        sys.stderr.write(f'>>> Wrong name of declared value\n')

    @staticmethod
    def p_type(p):
        """type : INT
                | CINT
                | BOOLEAN
                | CBOOLEAN
                | MAP """
        p[0] = node('type', val=p[1], ch=[])

    @staticmethod
    def p_assignment(p):
        """assignment : name EQUALS expression
                      | declaration EQUALS expression"""
        p[0] = node('assignment', ch=[p[1], p[3]])

    @staticmethod
    def p_assignment_err(p):
        """assignment : name EQUALS error"""
        p[0] = node('error', val="Wrong assignment")
        sys.stderr.write(f'>>> Wrong assignment\n')

    @staticmethod
    def p_name(p):
        """name : NAME"""
        p[0] = node('name', p[1])

    @staticmethod
    def p_number(p):
        """number : NUMBER"""
        p[0] = node('number', p[1])

    @staticmethod
    def p_expression(p):
        """expression : name
                      | const
                      | number
                      | logic_expression
                      | arithmetic_expression"""
        p[0] = p[1]

    @staticmethod
    def p_const(p):
        """const : TRUE
                 | FALSE
                        """
        p[0] = node('const', val=p[1])

    @staticmethod
    def p_logic_expression(p):
        """logic_expression : LT arithmetic_expression arithmetic_expression
                           | GT arithmetic_expression arithmetic_expression
                           | NOT logic_expression
                           | NOT call
                           | OR or_arg or_arg"""
        if len(p) == 4:
            p[0] = node('logic_expression', p[1], ch=[p[2], p[3]])
        else:
            p[0] = node('logic_expression', p[1], ch=p[2])

    @staticmethod
    def p_arithmetic_expression(p):
        """arithmetic_expression : INC first_ar second_ar
                                  | DEC first_ar second_ar"""
        p[0] = node('arithmetic_expression', p[1], ch=[p[2], p[3]])

    @staticmethod
    def p_first_ar(p):
        """first_ar : name
                  | arithmetic_expression
                  | call"""
        p[0] = p[1]

    @staticmethod
    def p_second_ar(p):
        """second_ar : name
                  | arithmetic_expression
                  | call
                  | number
                  | logic_expression
                  | const"""
        p[0] = p[1]

    @staticmethod
    def p_or_arg(p):
        """or_arg : call
                  | logic_expression
                  | TRUE
                  | FALSE"""
        p[0] = node('arg', p[1])

    @staticmethod
    def p_while(p):
        """while : WHILE logic_expression DO NEWLINE statements_group"""
        p[0] = node('while', ch={'condition': p[2], 'body': p[5]})

    @staticmethod
    def p_while_err(p):
        """while : DO error
                  | WHILE error"""
        p[0] = node('error', val="Wrong while")
        sys.stderr.write(f'>>> Wrong while\n')

    @staticmethod
    def p_if(p):
        """if : IF logic_expression NEWLINE statements_group
              | IF logic_expression NEWLINE statements_group ELSE statements_group"""
        if len(p) == 5:
            p[0] = node('if', ch={'condition': p[2], 'body': p[4]})
        else:
            p[0] = node('if', ch={'condition': p[2], 'body': p[4], 'else': p[6]})

    @staticmethod
    def p_if_err(p):
        """if : IF error"""
        p[0] = node('error', val="Wrong while")
        sys.stderr.write(f'>>> Wrong if\n')

    def p_procedure(self, p):
        """procedure : PROC NAME parameters NEWLINE statements_group """
        if p[2] in self._functions:
            sys.stderr.write(f'>>> function name duplicate at {p.lineno(4)} line\n')
            self.ok = False
        else:
           self._functions[p[2]] = node('procedure', ch={'parameters': p[3], 'body': p[5]})
           p[0] = node('function_description', val=p[2])

    @staticmethod
    def p_procedure_err(p):
        """procedure : PROC error"""
        p[0] = node('error', val="Wrong function name")
        sys.stderr.write(f'>>> Wrong function name at {p.lineno(2)} line\\n')

    @staticmethod
    def p_command_error(p):
        """command :  command error"""
        p[0] = node('error', val="Wrong command instruction")
        sys.stderr.write(f'>>> Wrong command instruction\n')

    @staticmethod
    def p_command(p):
        """command : LEFT
                    | RIGHT
                    | BACK
                    | STEP
                    | LOOK"""
        p[0] = node('robot', p[1])

    def p_call(self, p):
        """call : NAME parameters """
        if p[1] in self._functions:
            p[0] = node('call', p[1], ch=p[2])
        else:
            sys.stderr.write(f'>>> Unknown function name at {p.lineno(1)} line\n')
            self.ok = False

    @staticmethod
    def p_cell_proc(p):
        """cell_proc : BAR cell_arg
                     | EMP cell_arg
                     | SET cell_arg
                     | RESET cell_arg
                     | CLR cell_arg"""
        p[0] = node('call', p[1], ch=p[2])

    @staticmethod
    def p_cell_arg(p):
        """cell_arg : name name number number"""
        p[0] = node('parameters',  ch=[p[1], p[2], p[3], p[4]])

    @staticmethod
    def p_call_err0(p):
        """cell_proc :  BAR error
                     | EMP error
                     | SET error
                     | RESET error
                     | CLR error"""
        p[0] = node('error', val="Function call error")
        sys.stderr.write(f'>>> Function call error\n')

    @staticmethod
    def p_call_err(p):
        """call : NAME error """
        p[0] = node('error', val="Function call error")
        sys.stderr.write(f'>>> Function call error\n')

    @staticmethod
    def p_empty(p):
        """empty : """
        pass

    @staticmethod
    def p_parameters(p):
        """parameters : parameters name
                      | name"""
        if len(p) == 2:
            p[0] = node('parameters', ch=[p[1]])
        elif len(p) == 3:
            p[0] = node('parameters', ch=[p[1], p[2]])

    def p_error(self, p):
        try:
            sys.stderr.write(f'Syntax error at {p.lineno} line\n')
        except:
            sys.stderr.write(f'Syntax error\n')
        self.ok = False

    def get_f(self):
        return self._functions


if __name__ == '__main__':
    text = None
    f = open("C:/Users/user/PycharmProjects/lab2/factorial.txt")
    text = f.read()
    f.close()
    print(f'Your file:\n {text}')
    tree = node()
    text = text.upper()
    parser = parser()
    tree, func_table, correctness = parser.parse(text)
    if not correctness:
        sys.stderr.write(f'Can\'t interpretate incorrect algorithm\n')
    print(func_table)
    if tree==None:
        sys.stderr.write(f'Can\'t build the tree\n')
    else:
        tree.print()