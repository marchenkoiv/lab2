import sys
from tree import node as Node
import numpy
from Parser.parser import parser
from robot import Robot
from errors import Error_handler
from errors import InterpreterNameError
from errors import InterpreterConverseError
from errors import InterpreterValueError
from errors import InterpreterRedeclarationError

class Variable:
    def __init__(self, var_type='INT', var_value=None):
        self.type = var_type
        if self.type == 'BOOLEAN' or self.type == 'CBOOLEAN' :
            if var_value == "FALSE" or var_value==False:
                self.value = False
            elif var_value == "TRUE" or var_value==True:
                self.value = bool(True)
            else:
                self.value = var_value
        elif self.type == 'INT' or self.type == 'CINT' :
            if var_value == "FALSE" or var_value==False:
                self.value = 0
            elif var_value == "TRUE" or var_value==True:
                self.value = 1
            else:
                self.value = var_value
        else:
            self.value = var_value

    def __repr__(self):
        return f'{self.type}, {self.value}'


class Map:
    # 0 - unknown type
    # -1 - empty
    # 1 - wall
    def __init__(self, robot_m=None):
        self.type='MAP'
        if robot_m != None:
            self.origin_x = robot_m.x
            self.origin_y = robot_m.y
        else:
            self.origin_x = 0
            self.origin_y = 0
        self.map = numpy.array([[0],[0]])
        self.value = self.map




class Interpreter:

    def __init__(self, _parser=parser()):
        self.parser = _parser
        # DELETE ME
        self.sym_table = None
        self.scope = 0
        self.program = None
        self.fatal_error = False
        self.find_exit = False
        self.tree = None
        self.funcs = None
        self.robot = None
        self.error = Error_handler()
        self.error_types = {
            'UnexpectedError': 0,
            'NoInputPoint': 1,
            'RedeclarationError': 2,
            'UndeclaredError': 3,
            'FuncCallError': 4,
            'ConserveError': 5,
            'ValueError': 6,
            'WrongParameters': 7,
            'Recursion': 8,
            'TypeError': 9
        }

    def interpreter(self, _robot=None, program=None):
        self.robot = _robot
        self.program = program
        self.sym_table = [dict()]
        self.tree, self.funcs, _correctness = self.parser.parse(self.program)
        if _correctness:
            if self.tree.type != 'program':
                self.error.call(self.error_types['NoInputPoint'])
            try:
                self.interpreter_node(self.tree)
            except RecursionError:
                sys.stderr.write(f'RecursionError: function calls itself too many times\n')
                sys.stderr.write("========= Program has finished with fatal error =========\n")
        else:
            sys.stderr.write(f'Can\'t intemperate incorrect input file\n')

    @staticmethod
    def interpreter_tree(_tree):
        print("Program tree:\n")
        _tree.print()
        print("\n")

    def interpreter_node(self, node):

        if node is None:
            return
        # program
        if node.type == 'program':
            self.interpreter_node(node.child)
        # program - statements
        elif node.type == 'statements':
            try:
                for ch in node.child:
                    try:
                        self.interpreter_node(ch)
                        if self.fatal_error:
                            raise RecursionError from None
                    except RecursionError:
                        raise RecursionError from None
                    if self.fatal_error:
                        break
            except RecursionError:
                raise RecursionError from None

        elif node.type == 'error':
            self.error.call(self.error_types['UnexpectedError'], node)

        # STATEMENTS BLOCK

        # statements -> declaration
        elif node.type == 'declaration':
            if node.value != "MAP":
                declaration_type = node.value.value
                declaration_child = node.child[0]
                self.declare_variable(declaration_child, declaration_type)
                try:
                    declaration_value = self.interpreter_node(node.child[1])
                    if isinstance(declaration_value, bool):
                        declaration_value = Variable('BOOLEAN', declaration_value)
                    if isinstance(declaration_value, int):
                        declaration_value = Variable('INT', declaration_value)
                except InterpreterConverseError:
                    self.error.call(self.error_types['ConserveError'], node)
                    return
                except InterpreterValueError:
                    self.error.call(self.error_types['ValueError'], node)
                    return
                try:
                    self.assign(declaration_type, declaration_child.value, declaration_value)
                except InterpreterNameError:
                    self.error.call(self.error_types['UndeclaredError'], node)
                except InterpreterConverseError:
                    self.error.call(self.error_types['ConserveError'], node)
                except InterpreterValueError:
                    self.error.call(self.error_types['ValueError'], node)
                except RecursionError:
                    raise RecursionError from None
            else:
                declaration_type = node.value
                declaration_child = node.child
                self.declare_variable(declaration_child, declaration_type)


        # statements -> assignment
        elif node.type == 'assignment':
            variable = node.child[0].value
            if variable not in self.sym_table[self.scope].keys():
                self.error.call(self.error_types['UndeclaredError'], node)
            else:
                _type = self.sym_table[self.scope][variable].type
                try:
                    expression = self.interpreter_node(node.child[1])
                    if isinstance(expression, bool):
                        expression = Variable('BOOLEAN', expression)
                    if isinstance(expression, int):
                        expression = Variable('INT', expression)
                except InterpreterConverseError:
                    self.error.call(self.error_types['ConserveError'], node)
                    return
                except InterpreterValueError:
                    self.error.call(self.error_types['ValueError'], node)
                    return
                try:
                    self.assign(_type, variable, expression)
                    return expression
                except InterpreterNameError:
                    self.error.call(self.error_types['UndeclaredError'], node)
                except InterpreterConverseError:
                    self.error.call(self.error_types['ConserveError'], node)
                except InterpreterValueError:
                    self.error.call(self.error_types['ValueError'], node)
                except RecursionError:
                    raise RecursionError from None
        # statements -> while
        elif node.type == 'while':
            self.op_while(node)
        # statements -> if
        elif node.type == 'if':
            self.op_if(node)

        # statements -> robot
        elif node.type == 'robot':
            if node.value == 'BACK':
                return self.robot_back()
            elif node.value == 'LEFT':
                return self.robot_left()
            elif node.value == 'RIGHT':
                return self.robot_right()
            elif node.value == 'STEP':
                return self.robot_step()
            elif node.value == 'LOOK':
                return self.robot_look()

        # statements -> cell_proc
        elif node.type == 'cell_proc':
            try:
                if node.value == 'BAR':
                    return self.bar(node.child)
                elif node.value == 'EMP':
                    return self.emp(node.child)
                elif node.value == 'SET':
                    return self.set(node.child)
                elif node.value == 'RESET':
                    return self.reset(node.child)
                elif node.value == 'CLR':
                    return self.clr(node.child)
            except InterpreterValueError:
                self.error.call(self.error_types['WrongParameters'], node)
                return None

        # statements -> function
        elif node.type == 'procedure_description':
            pass

        # statements -> call
        elif node.type == 'call':
            try:
                return self.procedure_call(node)
            except RecursionError:
                raise RecursionError from None

        # EXPRESSION BLOCK

        # expression -> math_expression
        elif node.type == 'math_expression':
            try:
                if node.value == 'INC':
                    return self.increment(node.child[0], node.child[1])
                elif node.value == 'DEC':
                    return self.decrement(node.child[0], node.child[1])
                elif node.value == 'GT':
                    return self.gt(node.child[0], node.child[1])
                elif node.value == 'LT':
                    return self.lt(node.child[0], node.child[1])
                elif node.value == 'NOT':
                    return self.not_op(node.child)
                elif node.value == 'OR':
                    return self.or_op(node.child[0], node.child[1])
            except TypeError:
                self.error.call(self.error_types['TypeError'], node)

        # expression -> number
        elif node.type == 'number':
            return Variable('INT', node.value)

        # expression -> const
        elif node.type == 'const':
            return self.const_val(node.value)
        # expression / variables -> variable

        elif node.type == 'name':
            var = node.value
            if var not in self.sym_table[self.scope].keys():
                if var not in self.funcs:
                    i_is = -1
                    for i in range(len(self.sym_table) - 1, -1):
                        if var in self.sym_table[i].keys():
                            _is = i
                            break
                    if i_is > -1:
                        return self.sym_table[i_is][var]
                    self.error.call(self.error_types['UndeclaredError'], node)
                    return
                else:
                    return var
            return self.sym_table[self.scope][var]

    # for declaration
    def declare_variable(self, node, _type):
        try:
            self.declare(_type, node.value)
        except InterpreterRedeclarationError:
            self.error.call(self.error_types['RedeclarationError'], node)




    def declare(self, _type, _value):
        if _value in self.sym_table[self.scope].keys() or _value in self.funcs:
            raise InterpreterRedeclarationError
        if _type in ['INT', 'BOOLEAN', 'CINT', 'CBOOLEAN']:
            self.sym_table[self.scope][_value] = Variable(_type, None)
        else:
            self.sym_table[self.scope][_value] = Map(self.robot)

    def assign(self, _type, variable, expression: Variable):
        try:
            if expression is None:
                return
            if variable not in self.sym_table[self.scope].keys():
                raise InterpreterNameError
            elif (self.sym_table[self.scope][variable].type == 'CINT' or self.sym_table[self.scope][variable].type == 'CBOOLEAN') and self.sym_table[self.scope][variable].value != None:
                raise InterpreterConverseError
            elif _type == expression.type or ((_type == 'CINT' or _type == 'INT') and (expression.type=='CINT' or expression.type=='INT') or (_type=='CBOOLEAN' or _type=='BOOLEAN') and (expression.type=='CBOOLEAN' or expression.type=='BOOLEAN')):
                self.sym_table[self.scope][variable].value = expression.value
            elif (_type == 'CINT' or _type == 'INT') and (expression.type =='CBOOLEAN' or expression.type =='BOOLEAN'):
                self.sym_table[self.scope][variable].value = int(expression.value)
            else:
                raise InterpreterConverseError
        except RecursionError:
            raise RecursionError from None

    # for const
    @staticmethod
    def const_val(value):
        if (str(value)).isdigit():
            return Variable('INT', int(value))
        elif value in ['TRUE', 'FALSE', True, False]:
            return Variable('BOOLEAN', value)

    # for math operations

    # binary plus
    def increment(self, _val1, _val2):
        if isinstance(_val1, Node):
            _val1 = self.interpreter_node(_val1)
            _val2 = self.interpreter_node(_val2)
            if isinstance(_val1, Variable) and isinstance(_val2, Variable):
                if _val1.type == "INT" and (_val2.type == "INT" or _val2.type == "CINT"):
                    _val1.value = _val1.value + _val2.value
                    return _val1
                elif _val1.type == 'BOOLEAN' and (_val2.type == "BOOLEAN" or _val2.type == "CBOOLEAN"):
                    _val1.value = bool(_val1.value) or bool(_val2.value)
                    return _val1
                elif _val1.type == "INT" and (_val2.type == "BOOLEAN" or _val2.type == "CBOOLEAN"):
                    _val1.value = _val1.value + _val2.value
                    return _val1
       # _val1.value = _val1.value + _val2.value
        #return _val1
        raise TypeError

    # binary minus
    def decrement(self, _val1, _val2):
        if isinstance(_val1, Node):
            _val1 = self.interpreter_node(_val1)
            _val2 = self.interpreter_node(_val2)
            if isinstance(_val1, Variable) and isinstance(_val2, Variable):
                if _val1.type == "INT" and (_val2.type == "INT" or _val2.type == "CINT"):
                    _val1.value = _val1.value - _val2.value
                    return _val1
                elif _val1.type == 'BOOLEAN' and (_val2.type == "BOOLEAN" or _val2.type == "CBOOLEAN"):
                    _val1.value = bool(_val1.value) ^ bool(_val2.value)
                    return _val1
                elif _val1.type == "INT" and (_val2.type == "BOOLEAN" or _val2.type == "CBOOLEAN"):
                    _val1.value = _val1.value - _val2.value
                    return _val1
        #_val1.value = _val1.value - _val2.value
        #return _val1
        raise TypeError

    # binary greater
    def gt(self, _val1, _val2):
        expression1 = self.interpreter_node(_val1)
        expression2 = self.interpreter_node(_val2)
        if isinstance(expression1, Variable) and isinstance(expression2, Variable):
            return Variable('BOOLEAN', True) if expression1.value > expression2.value else Variable('BOOLEAN', False)
        else:
            return Variable('BOOLEAN', True) if expression1 > expression2 else Variable('BOOLEAN', False)

    # binary less
    def lt(self, _val1, _val2):
        expression1 = self.interpreter_node(_val1)
        expression2 = self.interpreter_node(_val2)
        if isinstance(expression1, Variable) and isinstance(expression2, Variable):
            return Variable('BOOLEAN', True) if expression1.value < expression2.value else Variable('BOOLEAN', False)
        else:
            return Variable('BOOLEAN', True) if expression1 > expression2 else Variable('BOOLEAN', False)

    # binary not
    def not_op(self, _val1):
        expression = self.interpreter_node(_val1)
        if isinstance(expression, Variable) and (expression.type == 'BOOLEAN' or expression.type == 'CBOOLEAN'):
            return Variable('BOOLEAN', not bool(expression.value))
        else:
            return Variable('BOOLEAN', not bool(expression))

    # binary or
    def or_op(self, _val1, _val2):
        expression1 = self.interpreter_node(_val1)
        expression2 = self.interpreter_node(_val2)
        if isinstance(expression1, Variable) and isinstance(expression2, Variable):
            return Variable('BOOLEAN', True) if expression1.value or expression2.value else Variable('BOOLEAN', False)
        else:
            return Variable('BOOLEAN', True) if expression1 or expression2 else Variable('BOOLEAN', False)

    # for robot

    def robot_left(self):
        return self.robot.left()

    def robot_right(self):
        return self.robot.right()

    def robot_back(self):
        return self.robot.back()

    def robot_step(self):
        k = self.robot.step()
        print('Robot:', interpreter.robot)
        if self.robot.is_exit():
            self.find_exit = True
            return -1
        return k

    def robot_look(self):
        return self.robot.look()

    #for cell_proc

    def bar(self, node):
        param = node.child
        try:
            var = self.interpreter_node(param[0])
            var_map = self.interpreter_node(param[1])
            var_x = self.interpreter_node(param[2])
            var_y = self.interpreter_node(param[3])
            if isinstance(var, Variable) and isinstance(var_map, Map) and isinstance(var_x, Variable) and isinstance(var_y, Variable) and var.type!='CINT' and var.type!='CBOOLEAN':
                if self.robot == None:
                    var.value = False
                    return False
                if numpy.shape(var_map.map)[1] <= var_map.origin_x - self.robot.x + var_x.value or var_map.origin_x - self.robot.x + var_x.value < 0 or numpy.shape(var_map.map)[0] <= var_map.origin_y - self.robot.y - var_y.value or var_map.origin_y - self.robot.y - var_y.value < 0:
                    if var.type == 'INT':
                        var.value = 0
                    else:
                        var.value = False
                    return var.value
                if var_map.map[var_map.origin_y - self.robot.y - var_y.value][var_map.origin_x - self.robot.x + var_x.value] == 1:
                    if var.type == 'INT':
                        var.value = 1
                    else:
                        var.value = True
                    return var.value
                else:
                    if var.type == 'INT':
                        var.value = 0
                    else:
                        var.value = False
                    return var.value
            raise InterpreterValueError
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)

    def emp(self, node):
        param = node.child
        try:
            var = self.interpreter_node(param[0])
            var_map = self.interpreter_node(param[1])
            var_x = self.interpreter_node(param[2])
            var_y = self.interpreter_node(param[3])
            if isinstance(var, Variable) and isinstance(var_map, Map) and isinstance(var_x, Variable) and isinstance(var_y, Variable) and var.type!='CINT' and var.type!='CBOOLEAN':
                if self.robot == None:
                    var.value = False
                    return False
                if numpy.shape(var_map.map)[1] <= var_map.origin_x - self.robot.x + var_x.value or var_map.origin_x - self.robot.x + var_x.value < 0 or numpy.shape(var_map.map)[0] <= var_map.origin_y - self.robot.y - var_y.value or var_map.origin_y - self.robot.y - var_y.value < 0:
                    if var.type == 'INT':
                        var.value = 0
                    else:
                        var.value = False
                    return var.value
                if var_map.map[var_map.origin_y - self.robot.y - var_y.value][var_map.origin_x - self.robot.x + var_x.value] == -1:
                    if var.type == 'INT':
                        var.value = 1
                    else:
                        var.value = True
                    return var.value
                else:
                    if var.type == 'INT':
                        var.value = 0
                    else:
                        var.value = False
                    return var.value
            raise InterpreterValueError
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)

    def set(self, node):
        param = node.child
        try:
            var = self.interpreter_node(param[0])
            var_map = self.interpreter_node(param[1])
            var_x = self.interpreter_node(param[2])
            var_y = self.interpreter_node(param[3])
            if isinstance(var, Variable) and isinstance(var_map, Map) and isinstance(var_x, Variable) and isinstance(var_y, Variable) and var.type != 'CINT' and var.type != 'CBOOLEAN':
                if self.robot == None:
                    var.value = False
                    return False
                elif numpy.shape(var_map.map)[1] > var_map.origin_x - self.robot.x + var_x.value and var_map.origin_x - self.robot.x + var_x.value > -1 and numpy.shape(var_map.map)[0] > var_map.origin_y - self.robot.y - var_y.value and var_map.origin_y - self.robot.y - var_y.value > -1:
                    var_map.map[var_map.origin_y -self.robot.y - var_y.value][var_map.origin_x - self.robot.x + var_x.value] = 1
                else:
                    x = var_map.origin_x - self.robot.x
                    y = var_map.origin_y - self.robot.y
                    if numpy.shape(var_map.map)[1] <= x + var_x.value:
                        a = numpy.zeros([numpy.shape(var_map.map)[0], x + var_x.value+1])
                        a[:numpy.shape(var_map.map)[0], :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.map = a
                    if x + var_x.value < 0:
                        a = numpy.zeros([numpy.shape(var_map.map)[0], numpy.shape(var_map.map)[1]-(x + var_x.value)])
                        a[:numpy.shape(var_map.map)[0],-(x + var_x.value):numpy.shape(var_map.map)[1]-(x + var_x.value)] = var_map.map
                        var_map.origin_x = var_map.origin_x - var_x.value - (x + var_x.value)
                        x = var_map.origin_x - self.robot.x
                        var_map.map = a
                    if len(var_map.map) <= y - var_y.value:
                        a = numpy.zeros([y - var_y.value+1, numpy.shape(var_map.map)[1]])
                        a[:numpy.shape(var_map.map)[0], :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.map = a
                    if y - var_y.value < 0:
                        a = numpy.zeros([numpy.shape(var_map.map)[0] - y + var_y.value, numpy.shape(var_map.map)[1]])
                        a[-(y - var_y.value):numpy.shape(var_map.map)[0]-(y - var_y.value), :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.origin_y = var_map.origin_y + var_y.value - y + var_y.value
                        y = var_map.origin_y - self.robot.y
                        var_map.map = a
                    var_map.map[y - var_y.value][x + var_x.value] = 1

                if var.type == 'INT':
                    var.value = 1
                else:
                    var.value = True
                return var.value
            raise InterpreterValueError
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)

    def reset(self, node):
        param = node.child
        try:
            var = self.interpreter_node(param[0])
            var_map = self.interpreter_node(param[1])
            var_x = self.interpreter_node(param[2])
            var_y = self.interpreter_node(param[3])
            if isinstance(var, Variable) and isinstance(var_map, Map) and isinstance(var_x, Variable) and isinstance(var_y, Variable) and var.type != 'CINT' and var.type != 'CBOOLEAN':
                if self.robot == None:
                    var.value = False
                    return False
                elif numpy.shape(var_map.map)[1] > var_map.origin_x - self.robot.x + var_x.value and var_map.origin_x - self.robot.x + var_x.value > -1 and numpy.shape(var_map.map)[0] > var_map.origin_y - self.robot.y - var_y.value and var_map.origin_y - self.robot.y - var_y.value > -1:
                    var_map.map[var_map.origin_y - self.robot.y - var_y.value][var_map.origin_x - self.robot.x + var_x.value] = 2
                else:
                    x = var_map.origin_x - self.robot.x
                    y = var_map.origin_y - self.robot.y
                    if numpy.shape(var_map.map)[1] <= x + var_x.value:
                        a = numpy.zeros([numpy.shape(var_map.map)[0], x + var_x.value + 1])
                        a[:numpy.shape(var_map.map)[0], :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.map = a
                    if x + var_x.value < 0:
                        a = numpy.zeros([numpy.shape(var_map.map)[0], numpy.shape(var_map.map)[1] - (x + var_x.value)])
                        a[:numpy.shape(var_map.map)[0], -(x + var_x.value):numpy.shape(var_map.map)[1] - (x + var_x.value)] = var_map.map
                        var_map.origin_x = var_map.origin_x - var_x.value- (x + var_x.value)
                        x = var_map.origin_x - self.robot.x
                        var_map.map = a
                    if len(var_map.map) <= y - var_y.value:
                        a = numpy.zeros([y - var_y.value + 1, numpy.shape(var_map.map)[1]])
                        a[:numpy.shape(var_map.map)[0], :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.map = a
                    if y - var_y.value < 0:
                        a = numpy.zeros([numpy.shape(var_map.map)[0] - y + var_y.value, numpy.shape(var_map.map)[1]])
                        a[-(y - var_y.value):numpy.shape(var_map.map)[0] - (y - var_y.value), :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.origin_y = var_map.origin_y + var_y.value - y + var_y.value
                        y = var_map.origin_y - self.robot.y
                        var_map.map = a
                    var_map.map[y - var_y.value][x + var_x.value] = 2

                if var.type == 'INT':
                    var.value = 1
                else:
                    var.value = True
                return var.value
            raise InterpreterValueError
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)

    def clr(self, node):
        param = node.child
        try:
            var = self.interpreter_node(param[0])
            var_map = self.interpreter_node(param[1])
            var_x = self.interpreter_node(param[2])
            var_y = self.interpreter_node(param[3])
            if isinstance(var, Variable) and isinstance(var_map, Map) and isinstance(var_x, Variable) and isinstance(
                    var_y, Variable) and var.type != 'CINT' and var.type != 'CBOOLEAN':
                if self.robot == None:
                    var.value = False
                    return False
                elif numpy.shape(var_map.map)[1] > var_map.origin_x - self.robot.x + var_x.value and var_map.origin_x - self.robot.x + var_x.value > -1 and numpy.shape(var_map.map)[0] > var_map.origin_y - self.robot.y - var_y.value and var_map.origin_y - self.robot.y - var_y.value > -1:
                    var_map.map[var_map.origin_y - self.robot.y - var_y.value][var_map.origin_x - self.robot.x + var_x.value] = 0
                else:
                    x = var_map.origin_x - self.robot.x
                    y = var_map.origin_y - self.robot.y
                    if numpy.shape(var_map.map)[1] <= x + var_x.value:
                        a = numpy.zeros([numpy.shape(var_map.map)[0], x + var_x.value + 1])
                        a[:numpy.shape(var_map.map)[0], :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.map = a
                    if x + var_x.value < 0:
                        a = numpy.zeros([numpy.shape(var_map.map)[0], numpy.shape(var_map.map)[1] - (x + var_x.value)])
                        a[:numpy.shape(var_map.map)[0], -(x + var_x.value):numpy.shape(var_map.map)[1] - (x + var_x.value)] = var_map.map
                        var_map.origin_x = var_map.origin_x - var_x.value - (x + var_x.value)
                        x = var_map.origin_x - self.robot.x
                        var_map.map = a
                    if len(var_map.map) <= y - var_y.value:
                        a = numpy.zeros([y - var_y.value + 1, numpy.shape(var_map.map)[1]])
                        a[:numpy.shape(var_map.map)[0], :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.map = a
                    if y - var_y.value < 0:
                        a = numpy.zeros([numpy.shape(var_map.map)[0] - y + var_y.value, numpy.shape(var_map.map)[1]])
                        a[-(y - var_y.value):numpy.shape(var_map.map)[0] - (y - var_y.value), :numpy.shape(var_map.map)[1]] = var_map.map
                        var_map.origin_y = var_map.origin_y + var_y.value - y + var_y.value
                        y = var_map.origin_y - self.robot.y
                        var_map.map = a
                    var_map.map[y - var_y.value][x + var_x.value] = 0

                if var.type == 'INT':
                    var.value = 1
                else:
                    var.value = True
                return var.value
            raise InterpreterValueError
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)


    # for while

    def op_while(self, node):
        try:
            while self.interpreter_node(node.child['condition']).value:
                self.interpreter_node(node.child['body'])
        except InterpreterConverseError:
            self.error.call(self.error_types['ConserveError'], node)
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)
        except InterpreterNameError:
            self.error.call(self.error_types['UndeclaredError'], node)
        except IndexError:
            self.error.call(self.error_types['UndeclaredError'], node)

    # for if

    def op_if(self, node):
        try:
            condition = self.interpreter_node(node.child['condition'])
            if condition.value:
                self.interpreter_node(node.child['body'])
            else:
                self.interpreter_node(node.child['else'])
        except InterpreterConverseError:
            self.error.call(self.error_types['ConserveError'], node)
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)
        except InterpreterNameError:
            self.error.call(self.error_types['UndeclaredError'], node)
        except IndexError:
            self.error.call(self.error_types['UndeclaredError'], node)

    # for functions

    def procedure_call(self, node):
        proc_name = node.value
        param = node.child
        proc_param = None
        inf_parameters = False
        named = True
        try:
            while isinstance(param, Node):
                if proc_param is None:
                    proc_param = []
                if len(param.child) > 1:
                    if param.child[1].child:
                        if not named:
                            raise InterpreterValueError
                        proc_param.append([param.child[1].value, self.interpreter_node(param.child[1].child)])
                    else:
                        named = False
                        proc_param.append(self.interpreter_node(param.child[1]))
                elif len(param.child) == 0:
                    break
                else:
                    if param.child[0].child:
                        if not named:
                            raise InterpreterValueError
                        proc_param.append([param.child[0].value, self.interpreter_node(param.child[0].child)])
                    else:
                        named = False
                        proc_param.append(self.interpreter_node(param.child[0]))
                param = param.child[0]
        except InterpreterConverseError:
            self.error.call(self.error_types['ConserveError'], node)
            return None
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)
            return None
        except InterpreterNameError:
            self.error.call(self.error_types['UndeclaredError'], node)
            return None
        except IndexError:
            self.error.call(self.error_types['UndeclaredError'], node)
        if proc_name not in self.funcs.keys() and proc_name not in self.sym_table[self.scope].keys():
            self.error.call(self.error_types['FuncCallError'], node)
            return None
        self.scope += 1
        self.sym_table.append(dict())
        if '#func' not in self.sym_table[0].keys():
            self.sym_table[0]['#func'] = 1
        else:
            self.sym_table[0]['#func'] += 1
        if self.sym_table[0]['#func'] > 100:
            raise RecursionError from None
        try:
            proc_subtree = self.funcs[proc_name] or self.funcs[self.sym_table[self.scope - 1][proc_name]]
        except KeyError:
            proc_subtree = self.funcs[self.sym_table[self.scope - 1][proc_name]]
        get = proc_subtree.child['parameters']
        proc_get = None
        while isinstance(get, Node):
            if proc_get is None:
                proc_get = []
            if len(get.child) == 1:
                try:
                    proc_get.append([get.child[0].value, None])
                except AttributeError:
                    self.error.call(self.error_types['WrongParameters'], node)
                    return None
                break
            if len(get.child) > 1:
                try:
                    proc_get.append([get.child[1].value, None])
                except AttributeError:
                    self.error.call(self.error_types['WrongParameters'], node)
                    return None
                get = get.child[0]
            if isinstance(get.child, Node):
                try:
                    proc_get.append([get.value, None])
                except AttributeError:
                    self.error.call(self.error_types['WrongParameters'], node)
                    return None
                proc_get.reverse()
                break
        if proc_get:
            for j in range(len(proc_get)):
                self.sym_table[self.scope][proc_get[j][0]] = proc_get[j][1]
        if proc_param:
            try:
                if proc_get:
                    for j in range(len(proc_get)):
                        if j < len(proc_param):
                            if isinstance(proc_param[j], Variable) or isinstance(proc_param[j], Map):
                                self.sym_table[self.scope][proc_get[j][0]] = proc_param[j]
                            else:
                                self.sym_table[self.scope][proc_get[j][0]] = proc_get[j][1]
                        else:
                            self.sym_table[self.scope][proc_get[j][0]] = proc_get[j][1]
                for j in range(len(proc_param)):
                    if isinstance(proc_param[j], list):
                        if proc_param[j][0] in self.sym_table[self.scope]:
                            self.sym_table[self.scope][proc_param[j][0]] = proc_param[j][1]
                        else:
                            raise TypeError
            except TypeError:
                self.error.call(self.error_types['WrongParameters'], node)
                self.sym_table.pop()
                self.scope -= 1
                return None
        if proc_param and proc_get and len(proc_get) != len(proc_param):
            self.error.call(self.error_types['WrongParameters'], node)
            self.sym_table.pop()
            self.scope -= 1
            return None
        result = None
        try:
            self.interpreter_node(proc_subtree.child['body'])
            result = self.sym_table[self.scope][param.value]
        except RecursionError:
            raise RecursionError from None
        except InterpreterConverseError:
            self.error.call(self.error_types['ConserveError'], node)
        except InterpreterValueError:
            self.error.call(self.error_types['ValueError'], node)
        except InterpreterNameError:
            self.error.call(self.error_types['UndeclaredError'], node)
        except IndexError:
            self.error.call(self.error_types['UndeclaredError'], node)
        self.sym_table[0]['#func'] -= 1
        self.scope -= 1
        self.sym_table.pop()
        return result


def create_robot(descriptor):
    _map = []
    with open(descriptor) as file:
        _text = file.readline().rstrip('\n')
        for line in file:
            _map.append(list(line.rstrip('\n')))

    # robot set
    x = int(_text[0])
    y = int(_text[2])
    turn = int(_text[4])

    return Robot(x=x, y=y, turn=turn, _map=_map)


if __name__ == '__main__':
    correct = False
    text = None
    isRobot = False
    file_num = 0
    while not correct:
        print("Input type? (file, robot)")
        inputType = input()
        correct = True
        if inputType == "file":
            robot = None
            f = open("C:/Users/user/PycharmProjects/lab2/factorial.txt")
            text = f.read()
            f.close()
            print(f'Your file:\n {text}')
        elif inputType == "robot":
            isRobot = True
            with open("C:/Users/user/PycharmProjects/lab2/right_hand.txt") as f:
                text = f.read()
            f.close()
            robot = create_robot("C:/Users/user/PycharmProjects/lab2/map.txt")
        else:
            print("I think, you're wrong :)")
            correct = False

    # prepare
    text = text.upper()
    parser = parser()
    tree, func_table, correctness = parser.parse(text)
    if correctness:

        interpreter = Interpreter()
        interpreter.interpreter(program=text, _robot=robot)
        print(f'Symbols table:\n')
        for sym_table in interpreter.sym_table:
            for keys, values in sym_table.items():
                if isinstance(values, Variable):
                    print(values.type, keys, '=', values.value)
                else:
                    if isinstance(values, Map):
                        print(keys, '\n', values.map)
        if isRobot:
            if interpreter.find_exit:
                print("\n\n========== END HAS BEEN FOUND ==========\n\n")
            else:
                print("\n\n========== END HAS NOT BEEN FOUND ==========\n\n")
            print('\nRobot:', interpreter.robot, '\n\n')
        print('\nerrors:')
    else:
        sys.stderr.write(f'Can\'t interpretate incorrect input file\n')