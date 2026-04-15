# Зависимости: pip install fonttools brotli

from fonttools import ...

# 1. Читает все SVG из src/glyphs/
# 2. Сопоставляет имя файла с Unicode-позицией
# 3. Собирает TTF через fonttools
# 4. Оптимизирует в woff2 через pyftsubset
# 5. Кладёт результат в dist/
