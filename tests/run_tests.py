"""Проверки конвейера и независимое исполнение его триад."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from compiler import pipeline
from common import CompileError
from triad_vm import execute


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    cases = json.loads((ROOT/'tests/cases.json').read_text(encoding='utf-8'))
    for c in cases:
        source = (ROOT/'tests'/c['file']).read_text(encoding='utf-8')
        try:
            data = pipeline(source, c['stage'])
            require(c['error'] is None, c['name'] + ': ошибка не обнаружена')
            if c['clean'] is not None:
                require(data['clean.cpp'] == c['clean'], c['name'])
        except CompileError as e:
            require(c['error'] and str(e).startswith(c['error']+':'), str(e))
        print(f"PASS {c['id']} {c['name']}")
    base = pipeline((ROOT/'test.cpp').read_text(encoding='utf-8'))
    require(len(base['tokens.json']) == 110, 'Количество токенов')
    require(all(set(t) == {'type', 'value'} for t in base['tokens.json']),
            'Токен должен содержать только два поля')
    require(len(base['lexemes.json']) == 8, 'Восемь таблиц лексем')
    require(len(base['symbols.json']) == 11, 'Количество символов')
    require(len(base['triads.json']) == 40, 'Количество триад')
    source = '// first\n\nint main() {\n    return absent;\n}\n'
    try:
        pipeline(source)
    except CompileError as e:
        require('строка 4, столбец 12' in str(e), 'Карта исходных координат')
    else:
        raise AssertionError('Необъявленная переменная')
    expected = ROOT/'docs/manual_triads.txt'
    require(base['triads.txt'] == expected.read_text(encoding='utf-8'),
            'Ручные триады не совпали с автоматическими')
    original = (ROOT/'test.cpp').read_text(encoding='utf-8')
    require(len(base['source_map.json']) == len(base['clean.cpp'])+1,
            'Координаты символов и EOF')
    print('PASS: 8 проверок структуры, координат и ручных триад')
    execution = json.loads((ROOT/'tests/execution.json').read_text(encoding='utf-8'))
    for c in execution:
        result = execute(pipeline(c['source'])['triads.json'])
        require(result == c['result'], c['name'])
        print(f"PASS VM {c['name']}: {result}")
    # Настоящие запуски каждого из четырёх комплектов вне рабочей папки проекта.
    with tempfile.TemporaryDirectory() as temp:
        td = Path(temp)
        for n in range(1, 5):
            lab = ROOT/f'Lab {n}'
            completed = subprocess.run([sys.executable, str(lab/'run.py'),
                str(lab/'test.cpp'), '--out', str(td/f'lab{n}')],
                cwd=td, capture_output=True, text=True, encoding='utf-8')
            require(completed.returncode == 0, completed.stdout+completed.stderr)
            print(f'PASS CLI Lab {n}')
        failed = td/'failed'
        completed = subprocess.run([sys.executable, str(ROOT/'compiler.py'),
            str(ROOT/'tests/fixtures/case_14.cpp'), '--out', str(failed)],
            cwd=td, capture_output=True, text=True, encoding='utf-8')
        require(completed.returncode == 1 and not failed.exists(),
                'Неуспешный запуск не должен создавать результат')
        print('PASS CLI: ошибка возвращает 1 и не создаёт результат')
        cpp = shutil.which('g++')
        if cpp:
            for name, source in [('original', original), ('clean', base['clean.cpp'])]:
                file = td/(name+'.cpp');file.write_text(source, encoding='utf-8')
                executable = td/(name+('.exe' if sys.platform=='win32' else ''))
                subprocess.run([cpp, '-std=c++17', str(file), '-o', str(executable)], check=True)
                actual = subprocess.run([str(executable)]).returncode
                require(actual == execute(base['triads.json']) == 8,
                        'Результат C++ должен совпадать с триадами')
                print(f'PASS g++ {name}: код возврата {actual}')
        else:
            print('SKIP g++: компилятор не установлен; Python-проверки выполнены')
    print(f'ИТОГО: {len(cases)} входов, 8 структурных проверок, '
          f'{len(execution)} исполнений триад, 5 CLI-проверок: успешно.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
