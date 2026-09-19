"""Общие ошибки и координаты исходного текста."""
class CompileError(Exception):
    pass


def location(text, offset):
    line = text.count('\n', 0, offset) + 1
    column = offset - text.rfind('\n', 0, offset)
    return line, column


def fail(stage, pos, message):
    line, column = pos
    raise CompileError(
        f'{stage}: строка {line}, столбец {column}: {message}'
    )
