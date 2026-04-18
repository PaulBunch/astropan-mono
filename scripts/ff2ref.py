#!/usr/bin/env python3
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Регистрируем пространства имен, чтобы избежать мусора в итоговом файле
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def format_ff_name(filename_stem):
    """
    Приводит имя файла из FontForge к структурированному виду.
    Ожидает формат: 'u1F319_Quivira' -> возвращает 'quivira_u1f319'
    """
    parts = filename_stem.split('_')
    if len(parts) >= 2:
        # Если первая часть похожа на юникод (u + шестнадцатеричный код)
        if re.match(r'^u[0-9a-fA-F]+$', parts[0]):
            return f"{parts[1].lower()}_{parts[0].lower()}"

    # Фолбек: просто приводим к нижнему регистру
    return filename_stem.lower()


def clean_element(element):
    """
    Очищает атрибуты. Специально удаляем fill (например, 'currentColor'),
    чтобы путь унаследовал черную полупрозрачную заливку от группы.
    """
    geometry_attrs = {
        'd', 'viewBox', 'xmlns', 'xmlns:xlink', 'fill-rule', 'clip-rule',
        'transform', 'version'
    }
    for attr in list(element.attrib):
        if attr not in geometry_attrs:
            del element.attrib[attr]


def process_ff_svg(file_path):
    """
    Парсит SVG из FontForge, жестко масштабирует относительно UPM,
    сохраняя координаты базовой линии и апрошей.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing {file_path.name}: {e}")
        return None

    viewbox = root.get('viewBox')
    if not viewbox:
        print(f"Skipping {file_path.name}: No viewBox found.")
        return None

    vb = [float(x) for x in viewbox.split()]
    try:
        # Высота viewBox в экспорте FontForge — это всегда UPM шрифта (например, 2048)
        min_x, _min_y, width, upm = vb[0], vb[1], vb[2], vb[3]
    except IndexError:
        print(f"Skipping {file_path.name}: Invalid viewBox.")
        return None

    # 1. Рассчитываем масштаб
    # Математика сохранения метрик: масштабируем строго относительно UPM
    scale = 1000 / upm

    # 2. Рассчитываем горизонтальный сдвиг для центровки advance_width
    # Находим центр исходной площадки в новых координатах и двигаем его к 500
    scaled_center_x = (min_x + width / 2) * scale
    dx = 500 - scaled_center_x

    # 3. Группа трансформации
    # Создаем группу, которая задает цвет и применяет масштаб к координатам.
    # Сначала масштабируем, потом двигаем (в SVG translate применяется после scale)
    wrapper = ET.Element('g', {
        'id': 'glyph',
        'transform': f'translate({dx:.2f}, 0) scale({scale:.4f})',
        'fill': 'black',
        'fill-opacity': '0.2'
    })

    for child in list(root):
        root.remove(child)
        wrapper.append(child)
        clean_element(child)

    root.append(wrapper)

    # Фиксируем холст на нашем эталонном размере
    root.set('viewBox', '0 0 1000 1000')
    clean_element(root)

    formatted_name = format_ff_name(file_path.stem)
    return formatted_name, ET.tostring(root, encoding='unicode')


def main():
    parser = argparse.ArgumentParser(description="FontForge SVG to Reference Template Converter")
    parser.add_argument("input", help="Path to input directory containing FF SVGs (or a single SVG file)")
    parser.add_argument("-o", "--output", default="src/references/fontforge", help="Output directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Поддержка как директории с файлами, так и одиночного файла
    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = list(input_path.glob("*.svg"))
    else:
        print(f"Path not found: {input_path}")
        sys.exit(1)

    print(f"Found {len(files)} FontForge SVGs. Processing...")

    for file_path in files:
        result = process_ff_svg(file_path)
        if result:
            name, clean_content = result
            out_file = output_dir / f"{name}.svg"
            out_file.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + clean_content)
            print(f"  [OK] {file_path.name} -> {out_file.name}")


if __name__ == "__main__":
    main()
