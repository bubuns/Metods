"""ЛР 3. Рекурсивный спуск и построение AST."""
from common import fail

LITERALS = {'CONSTANT_INT': 'int', 'CONSTANT_REAL': 'double',
            'CONSTANT_BOOL': 'bool', 'CONSTANT_STRING': 'string'}
LEVELS = [('||',), ('&&',), ('==', '!='),
          ('<', '<=', '>', '>='), ('+', '-'), ('*', '/')]


class Parser:
    def __init__(self, tokens, positions):
        self.tokens = tokens + [{'type': 'EOF', 'value': '<EOF>'}]
        self.positions = positions
        self.i = 0

    def peek(self):
        return self.tokens[self.i]['value']

    def node(self, kind, at, **fields):
        return dict(kind=kind, pos=self.positions[at], **fields)

    def error(self, expected):
        fail('SYNTAX', self.positions[self.i],
             f'ожидалось {expected}, получено {self.peek()!r}')

    def take(self, value=None, kind=None):
        token = self.tokens[self.i]
        if ((value is not None and token['value'] != value)
                or (kind is not None and token['type'] != kind)):
            self.error(repr(value) if value else kind)
        self.i += 1
        return token['value']

    def accept(self, value):
        if self.peek() != value:
            return False
        self.take(value)
        return True

    def type_name(self):
        if self.peek() in {'int', 'double', 'bool'}:
            return self.take()
        if self.accept('const'):
            self.take('char')
            self.take('*')
            return 'string'
        self.error('тип int, double, bool или const char*')

    def parse(self):
        functions = []
        while self.peek() != '<EOF>':
            functions.append(self.function())
        return self.node('Program', 0, functions=functions)

    def function(self):
        at = self.i
        typ = self.type_name()
        name = self.take(kind='IDENTIFIER')
        self.take('(')
        params = []
        if self.peek() != ')':
            while True:
                p = self.i
                pt = self.type_name()
                pn = self.take(kind='IDENTIFIER')
                params.append(self.node('Param', p, name=pn, type=pt))
                if not self.accept(','):
                    break
        self.take(')')
        return self.node('Function', at, name=name, type=typ,
                         params=params, body=self.block())

    def block(self):
        at = self.i
        self.take('{')
        body = []
        while self.peek() != '}':
            if self.peek() == '<EOF>':
                self.error("'}' для завершения блока")
            body.append(self.statement())
        self.take('}')
        return self.node('Block', at, body=body)

    def statement(self):
        at = self.i
        value = self.peek()
        if value in {'int', 'double', 'bool', 'const'}:
            return self.declaration()
        if value == 'if':
            return self.if_statement()
        if value == 'while':
            return self.while_statement()
        if value == '{':
            return self.block()
        if self.accept('return'):
            expr = self.expression()
            self.take(';')
            return self.node('Return', at, expr=expr)
        if (self.tokens[self.i]['type'] == 'IDENTIFIER'
                and self.tokens[self.i + 1]['value'] == '='):
            name = self.take(kind='IDENTIFIER')
            self.take('=')
            expr = self.expression()
            self.take(';')
            return self.node('Assign', at, name=name, expr=expr)
        expr = self.expression()
        self.take(';')
        return self.node('ExprStmt', at, expr=expr)

    def declaration(self):
        at = self.i
        typ = self.type_name()
        name = self.take(kind='IDENTIFIER')
        expr = self.expression() if self.accept('=') else None
        self.take(';')
        return self.node('VarDecl', at, name=name, type=typ, expr=expr)

    def if_statement(self):
        at = self.i
        self.take('if')
        self.take('(')
        cond = self.expression()
        self.take(')')
        yes = self.block()
        no = self.block() if self.accept('else') else None
        return self.node('If', at, cond=cond, yes=yes, no=no)

    def while_statement(self):
        at = self.i
        self.take('while')
        self.take('(')
        cond = self.expression()
        self.take(')')
        return self.node('While', at, cond=cond, body=self.block())

    def expression(self, level=0):
        if level == len(LEVELS):
            return self.unary()
        at = self.i
        left = self.expression(level + 1)
        while self.peek() in LEVELS[level]:
            op = self.take()
            right = self.expression(level + 1)
            left = self.node('Binary', at, op=op,
                             left=left, right=right)
        return left

    def unary(self):
        at = self.i
        if self.peek() in {'!', '-', '+'}:
            op = self.take()
            return self.node('Unary', at, op=op, expr=self.unary())
        return self.primary()

    def primary(self):
        at = self.i
        token = self.tokens[self.i]
        if token['type'] in LITERALS:
            self.take()
            return self.node('Literal', at, value=token['value'],
                             type=LITERALS[token['type']])
        if token['type'] == 'IDENTIFIER':
            name = self.take()
            if not self.accept('('):
                return self.node('Name', at, name=name)
            args = []
            if self.peek() != ')':
                while True:
                    args.append(self.expression())
                    if not self.accept(','):
                        break
            self.take(')')
            return self.node('Call', at, name=name, args=args)
        if self.accept('('):
            expr = self.expression()
            self.take(')')
            return expr
        self.error('идентификатор, константа или выражение в скобках')
