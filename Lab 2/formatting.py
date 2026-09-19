"""Читаемые представления результатов анализаторов."""
import json


def table(headers, rows):
    rows = [[str(x) for x in row] for row in rows]
    widths = [max(len(h), *(len(row[i]) for row in rows))
              if rows else len(h) for i, h in enumerate(headers)]
    def line(row):
        return ' | '.join(x.ljust(w) for x, w in zip(row, widths))
    return '\n'.join([line(headers), '-+-'.join('-' * w for w in widths)]
                     + [line(row) for row in rows]) + '\n'


def lexeme_tables(tokens):
    kinds = ['KEYWORD', 'IDENTIFIER', 'CONSTANT_INT', 'CONSTANT_REAL',
             'CONSTANT_STRING', 'CONSTANT_BOOL', 'OPERATOR', 'DELIMITER']
    result = {}
    for kind in kinds:
        values = dict.fromkeys(t['value'] for t in tokens if t['type'] == kind)
        result[kind] = [dict(id=i, value=v)
                        for i, v in enumerate(values, 1)]
    return result


def token_text(tokens):
    return table(['N', 'TYPE', 'VALUE'],
                 [(i, t['type'], t['value'])
                  for i, t in enumerate(tokens, 1)])


def lexeme_text(tables):
    return '\n'.join(kind + '\n' + table(['id', 'value'],
                    [(t['id'], t['value']) for t in rows])
                    for kind, rows in tables.items())


def ast_lines(node, prefix=''):
    attrs = [f'{k}={node[k]}' for k in ['name', 'type', 'op', 'value']
             if k in node]
    yield prefix + node['kind'] + (' ' + ', '.join(attrs) if attrs else '')
    for key, value in node.items():
        if key in ['kind', 'pos', 'name', 'type', 'op', 'value']:
            continue
        if isinstance(value, dict):
            child = list(ast_lines(value, prefix + '    '))
            yield prefix + '  ' + key + ': ' + child[0].strip()
            yield from child[1:]
        elif isinstance(value, list):
            yield prefix + '  ' + key + ':'
            for item in value:
                yield from ast_lines(item, prefix + '    ')
        elif value is None:
            yield prefix + '  ' + key + ': null'


def symbol_text(symbols):
    return table(['NAME', 'TYPE', 'SCOPE', 'LINE', 'KIND', 'INIT'],
                 [(s['name'], s['type'], s['scope'], s['line'],
                   s['kind'], s['initialized']) for s in symbols])


def save_results(data, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in data.items():
        content = (json.dumps(value, ensure_ascii=False, indent=2) + '\n'
                   if name.endswith('.json') else value)
        (directory / name).write_text(content, encoding='utf-8')
