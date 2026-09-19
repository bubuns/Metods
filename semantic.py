"""ЛР 4. Проверка AST, таблица символов и генерация триад."""
from common import fail

NUMERIC = {'int', 'double'}


class Semantic:
    def __init__(self):
        self.functions = {}
        self.scopes = []
        self.symbols = []
        self.initialized = set()
        self.triads = []
        self.counter = 0
        self.function = None

    def error(self, node, text):
        fail('SEMANTIC', node['pos'], text)

    def emit(self, op, a='-', b='-'):
        self.triads.append([op, str(a), str(b)])
        return '^' + str(len(self.triads))

    def label(self):
        self.counter += 1
        return 'L' + str(self.counter)

    def convert(self, expected, actual, value, node):
        if expected == actual:
            return value
        if expected == 'double' and actual == 'int':
            return self.emit('I2D', value)
        self.error(node, f'несовместимые типы: {expected} <- {actual}')

    def declare(self, node, parameter=False):
        name = node['name']
        if name in self.scopes[-1]:
            self.error(node, f'повторное объявление {name}')
        line, col = node['pos']
        uid = f"{self.function['name']}/{name}@{line}:{col}"
        symbol = dict(name=name, type=node['type'], uid=uid,
                      scope=self.function['name'], depth=len(self.scopes),
                      line=node['pos'][0], kind='param' if parameter
                      else 'variable', initialized=parameter)
        self.scopes[-1][name] = symbol
        self.symbols.append(symbol)
        if parameter:
            self.initialized.add(uid)
        return symbol

    def resolve(self, node):
        for scope in reversed(self.scopes):
            if node['name'] in scope:
                return scope[node['name']]
        self.error(node, f"необъявленная переменная {node['name']}")

    def expr(self, node):
        kind = node['kind']
        if kind == 'Literal':
            return node['type'], node['value']
        if kind == 'Name':
            symbol = self.resolve(node)
            if symbol['uid'] not in self.initialized:
                self.error(node, f"нет инициализации {node['name']}")
            return symbol['type'], symbol['uid']
        if kind == 'Call':
            if any(node['name'] in s for s in self.scopes):
                self.error(node, f"{node['name']} является переменной")
            fn = self.functions.get(node['name'])
            if fn is None:
                self.error(node, f"необъявленная функция {node['name']}")
            if len(node['args']) != len(fn['params']):
                self.error(node, 'неверное количество аргументов')
            args = []
            for arg, param in zip(node['args'], fn['params']):
                typ, value = self.expr(arg)
                args.append(self.convert(param['type'], typ, value, arg))
            # Сначала вычисляются все аргументы, затем PARAM.
            for i, value in enumerate(args):
                self.emit('PARAM', value, i)
            return fn['type'], self.emit('CALL', fn['name'], len(args))
        if kind == 'Unary':
            typ, value = self.expr(node['expr'])
            op = node['op']
            if (op == '!' and typ != 'bool') or (
                    op in {'+', '-'} and typ not in NUMERIC):
                self.error(node, f'операция {op} недопустима для {typ}')
            return typ, self.emit({'!': 'NOT', '-': 'NEG',
                                   '+': 'POS'}[op], value)
        if kind != 'Binary':
            self.error(node, f'неизвестное выражение {kind}')
        op = node['op']
        lt, left = self.expr(node['left'])
        if op in {'&&', '||'}:
            if lt != 'bool':
                self.error(node, 'логический операнд должен иметь тип bool')
            end = self.label()
            temp = '$' + end
            self.emit(':=', temp, left)
            self.emit('JF' if op == '&&' else 'JT', left, '@' + end)
            rt, right = self.expr(node['right'])
            if rt != 'bool':
                self.error(node, 'логический операнд должен иметь тип bool')
            self.emit(':=', temp, right)
            self.emit('LABEL', end)
            return 'bool', temp
        rt, right = self.expr(node['right'])
        if op in {'==', '!='} and lt == rt == 'bool':
            return 'bool', self.emit(op, left, right)
        if lt not in NUMERIC or rt not in NUMERIC:
            self.error(node, f'операция {op}: несовместимые {lt}, {rt}')
        typ = 'double' if 'double' in {lt, rt} else 'int'
        left = self.convert(typ, lt, left, node)
        right = self.convert(typ, rt, right, node)
        result = self.emit(op, left, right)
        return ('bool' if op in {'<', '<=', '>', '>=', '==', '!='}
                else typ), result

    def condition(self, node):
        typ, value = self.expr(node)
        if typ != 'bool':
            self.error(node, 'условие должно иметь тип bool')
        return value

    def block(self, node, nested=True):
        if nested:
            self.scopes.append({})
        returned = False
        for stmt in node['body']:
            if returned:
                self.error(stmt, 'недостижимый оператор после return')
            returned = self.statement(stmt)
        if nested:
            local = self.scopes.pop()
            for symbol in local.values():
                symbol['initialized'] = symbol['uid'] in self.initialized
                self.initialized.discard(symbol['uid'])
        return returned

    def statement(self, node):
        kind = node['kind']
        if kind == 'Block':
            return self.block(node)
        if kind in {'VarDecl', 'Assign'}:
            symbol = (self.declare(node) if kind == 'VarDecl'
                      else self.resolve(node))
            if node['expr'] is not None:
                typ, value = self.expr(node['expr'])
                value = self.convert(symbol['type'], typ, value, node)
                self.emit(':=', symbol['uid'], value)
                self.initialized.add(symbol['uid'])
        elif kind == 'ExprStmt':
            self.expr(node['expr'])
        elif kind == 'Return':
            typ, value = self.expr(node['expr'])
            value = self.convert(self.function['type'], typ, value, node)
            self.emit('RET', value)
            return True
        elif kind == 'If':
            cond = self.condition(node['cond'])
            no, end = self.label(), self.label()
            before = self.initialized.copy()
            self.emit('JF', cond, '@' + no)
            yes_returns = self.block(node['yes'])
            after_yes = self.initialized.copy()
            self.emit('JMP', '@' + end)
            self.emit('LABEL', no)
            self.initialized = before.copy()
            no_returns = self.block(node['no']) if node['no'] else False
            after_no = self.initialized.copy()
            if yes_returns:
                self.initialized = after_no
            elif no_returns:
                self.initialized = after_yes
            else:
                self.initialized = after_yes & after_no
            self.emit('LABEL', end)
            return yes_returns and no_returns
        elif kind == 'While':
            start, end = self.label(), self.label()
            before = self.initialized.copy()
            self.emit('LABEL', start)
            cond = self.condition(node['cond'])
            self.emit('JF', cond, '@' + end)
            self.block(node['body'])
            self.emit('JMP', '@' + start)
            self.emit('LABEL', end)
            # Цикл может не выполниться ни разу.
            self.initialized = before
        else:
            self.error(node, f'неизвестный оператор {kind}')
        return False

    def analyze(self, root):
        for fn in root['functions']:
            name = fn['name']
            if name in self.functions:
                self.error(fn, f'повторное определение функции {name}')
            self.functions[name] = fn
            self.function = fn
            self.symbols.append(dict(name=name, type=fn['type'],
                uid=name, scope='global', depth=0, line=fn['pos'][0],
                kind='function', initialized=True))
            self.scopes = [{}]
            self.initialized = set()
            self.emit('FUNC', name, fn['type'])
            for index, param in enumerate(fn['params']):
                symbol = self.declare(param, parameter=True)
                self.emit('ARG', symbol['uid'], index)
            returned = self.block(fn['body'], nested=False)
            if not returned:
                self.error(fn, 'не на всех путях возвращается значение')
            for symbol in self.scopes[0].values():
                symbol['initialized'] = symbol['uid'] in self.initialized
            self.emit('END', name)
        main = self.functions.get('main')
        if main is None or main['type'] != 'int' or main['params']:
            self.error(root, 'нужна точка входа int main()')
        return self.symbols, self.triads
