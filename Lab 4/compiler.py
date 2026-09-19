"""Общий запуск четырёх этапов компилятора."""
import argparse
from pathlib import Path
from common import CompileError
from preprocessor import preprocess
from formatting import (lexeme_tables, lexeme_text, token_text,
                        ast_lines, symbol_text, save_results)


def pipeline(source, stage='all'):
    clean, mapping = preprocess(source)
    data = {'clean.cpp': clean, 'source_map.json': mapping}
    if stage == 'pre':
        return data
    from lexer import lex
    tokens, positions = lex(clean, mapping)
    tables = lexeme_tables(tokens)
    data.update({'tokens.json': tokens, 'positions.json': positions,
                 'tokens.txt': token_text(tokens),
                 'lexemes.json': tables, 'lexemes.txt': lexeme_text(tables)})
    if stage == 'lex':
        return data
    from parser import Parser
    ast = Parser(tokens, positions).parse()
    data['ast.json'] = ast
    data['ast.txt'] = '\n'.join(ast_lines(ast)) + '\n'
    if stage == 'parse':
        return data
    from semantic import Semantic
    symbols, triads = Semantic().analyze(ast)
    data['symbols.json'] = symbols
    data['symbols.txt'] = symbol_text(symbols)
    data['triads.json'] = triads
    data['triads.txt'] = '\n'.join(
        f'{i}) {op} ({a}, {b})'
        for i, (op, a, b) in enumerate(triads, 1)) + '\n'
    return data


def main(default_stage='all'):
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--stage', default=default_stage,
                        choices=['pre', 'lex', 'parse', 'all'])
    parser.add_argument('--out', type=Path, default=Path('build'))
    args = parser.parse_args()
    try:
        source = args.source.read_text(encoding='utf-8')
        data = pipeline(source, args.stage)
        # Файлы создаются только после успешного выбранного этапа.
        save_results(data, args.out)
        print(f'Этап {args.stage}: успешно. Ошибок не найдено.')
        if 'tokens.json' in data:
            print(f"Токенов: {len(data['tokens.json'])}")
        if 'symbols.json' in data:
            print(f"Символов: {len(data['symbols.json'])}")
            print(f"Триад: {len(data['triads.json'])}")
        print(f'Результаты: {args.out}')
        return 0
    except (CompileError, OSError, UnicodeError) as error:
        print(error)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(default_stage='all'))
