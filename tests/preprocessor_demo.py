"""Наглядная проверка сохранения строк и границ лексем."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preprocessor import preprocess

for source in ['const char* s="http://x /* y */  z";', 'int/**/x;']:
    print('Вход: ', source)
    print('Выход:', preprocess(source)[0].rstrip())
