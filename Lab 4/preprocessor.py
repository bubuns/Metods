"""ЛР 1. Очистка текста с сохранением содержимого строк."""
import re
from common import fail, location

STRING = r'"(?:\\[^\n]|[^"\\\n])*"'
PARTS = re.compile(
    STRING + r'|//[^\n]*|/\*[\s\S]*?(?:\*/|\Z)'
    r'|"(?:\\[^\n]|[^"\\\n])*(?=\n|\Z)'
    r'|[ \t]+|\n|.', re.DOTALL
)
BAD = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def preprocess(source):
    source = source.replace('\r\n', '\n').replace('\r', '\n')
    bad = BAD.search(source)
    if bad:
        fail('PREPROCESS', location(source, bad.start()),
             f'недопустимый символ U+{ord(bad[0]):04X}')
    chars, origins = [], []
    for match in PARTS.finditer(source):
        value = match[0]
        start = match.start()
        if value.startswith('//'):
            value = ' '
        elif value.startswith('/*'):
            if not value.endswith('*/'):
                fail('PREPROCESS', location(source, start),
                     'незакрытый многострочный комментарий')
            # Комментарий заменяется пробелом, а не пустотой.
            for j, c in enumerate(value):
                if j == 0 and chars and chars[-1] == ' ':
                    continue
                if j == 0 or c == '\n':
                    chars.append(' ' if j == 0 else '\n')
                    origins.append(start + j)
            continue
        elif re.fullmatch(r'[ \t]+', value):
            value = ' '
        if value == ' ' and chars and chars[-1] == ' ':
            continue
        for j, c in enumerate(value):
            chars.append(c)
            origins.append(start + j)
    # Удаление отступов и пустых строк после защиты литералов.
    text = ''.join(chars)
    clean, mapping = [], []
    for match in re.finditer(r'[^\n]+', text):
        row = match[0]
        left = len(row) - len(row.lstrip(' '))
        right = len(row.rstrip(' '))
        if left >= right:
            continue
        a, b = match.start() + left, match.start() + right
        clean.extend(chars[a:b] + ['\n'])
        mapping.extend(origins[a:b] + [origins[b - 1]])
    mapping.append(len(source))  # Координаты EOF.
    return ''.join(clean), [location(source, p) for p in mapping]
