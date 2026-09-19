"""ЛР 2. Токены имеют ровно два поля; позиции хранятся отдельно."""
import re
from common import fail, location
from preprocessor import STRING
KEYWORDS = {'int', 'double', 'bool', 'const', 'char',
            'if', 'else', 'while', 'return'}
OPERATORS = {'=', '+', '-', '*', '/', '<', '<=', '>', '>=',
             '==', '!=', '&&', '||', '!'}
DELIMITERS = set('(){};,')
PATTERN = re.compile(
    r'(?P<SPACE>\s+)|(?P<CONSTANT_STRING>' + STRING + r')|'
    r'(?P<NUMBER>[0-9][A-Za-z_0-9.]*)|'
    r'(?P<IDENTIFIER>[A-Za-z_][A-Za-z_0-9]*)|'
    r'(?P<OPERATOR>\+\+|--|\+=|-=|\*=|/=|<<|>>|'
    r'<=|>=|==|!=|&&|\|\||[=+*/<>!&|%^-])|'
    r'(?P<DELIMITER>[(){};,])|(?P<BAD>.)', re.DOTALL
)

def lex(text, source_map=None):
    tokens, positions = [], []
    for match in PATTERN.finditer(text):
        kind, value = match.lastgroup, match[0]
        pos = (source_map[match.start()] if source_map
               else location(text, match.start()))
        if kind == 'SPACE':
            continue
        if kind == 'BAD':
            reason = ('незакрытая строковая константа'
                      if value == '"' else
                      f'недопустимый символ {value!r}')
            fail('LEXICAL', pos, reason)
        if kind == 'NUMBER':
            if re.fullmatch(r'(0|[1-9][0-9]*)', value):
                kind = 'CONSTANT_INT'
            elif re.fullmatch(r'[0-9]+\.[0-9]+', value):
                kind = 'CONSTANT_REAL'
            else:
                fail('LEXICAL', pos,
                     f'неверное число или имя с цифры: {value!r}')
        elif kind == 'IDENTIFIER':
            if value in {'true', 'false'}:
                kind = 'CONSTANT_BOOL'
            elif value in KEYWORDS:
                kind = 'KEYWORD'
        elif kind == 'OPERATOR' and value not in OPERATORS:
            fail('LEXICAL', pos,
                 f'неподдерживаемый оператор {value!r}')
        elif kind == 'CONSTANT_STRING':
            if re.search(r'\\[^ntr"\\]', value):
                fail('LEXICAL', pos,
                     'недопустимая escape-последовательность')
        tokens.append({'type': kind, 'value': value})
        positions.append(pos)
    eof = source_map[-1] if source_map else location(text, len(text))
    return tokens, positions + [eof]
