#!/usr/bin/env python3
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Регистрируем пространство имен
ET.register_namespace("", "http://www.w3.org/2000/svg")


def get_unique_name(name_registry, raw_name):
    """Очищает имя и гарантирует уникальность."""
    # Оставляем только буквы и цифры, приводим к нижнему регистру
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', raw_name).strip('_').lower()
    if not clean_name:
        clean_name = "glyph"

    # Проверка на дубликаты
    if clean_name not in name_registry:
        name_registry[clean_name] = 1
        return clean_name
    else:
        name_registry[clean_name] += 1
        return f"{clean_name}_{name_registry[clean_name]}"


def clean_element(element):
    """Очищает атрибуты, сохраняя критически важные для формы."""
    # Атрибуты, влияющие на геометрию и логику отрисовки
    geometry_attrs = {
        'd', 'viewBox', 'xmlns', 'fill-rule', 'clip-rule',
        'cx', 'cy', 'r', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'transform'
    }

    # Очистка корневого элемента
    for attr in list(element.attrib):
        if attr not in geometry_attrs:
            del element.attrib[attr]


def process_svg(name_registry, svg_string, index):
    """Парсит, масштабирует с сохранением пропорций и центрирует в 1000x1000."""
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError as e:
        print(f"Error parsing SVG #{index}: {e}")
        return None

    # 1. Извлечение имени
    raw_id = root.get('id') or root.get('data-test-id') or f"glyph_{index}"
    # Пытаемся вытащить осмысленную часть из длинных ID (напр. Taurus)
    potential_name = re.search(r'([A-Z][a-z]+)', raw_id)
    name_base = potential_name.group(1) if potential_name else raw_id.split('-')[-1]
    final_name = get_unique_name(name_registry, name_base)

    # 2. Масштабирование без смещения (Preserve Positioning)
    viewbox = root.get('viewBox', '0 0 24 24').split()
    try:
        orig_w = float(viewbox[2])
        orig_h = float(viewbox[3])
    except (IndexError, ValueError):
        orig_w, orig_h = 24, 24

    # Масштаб по самой длинной стороне
    scale = 1000 / max(orig_w, orig_h)

    # 3. Создаем группу с заливкой и масштабом
    wrapper = ET.Element('g', {
        'transform': f'scale({scale:.4f})',
        'fill': 'black',
        'fill-opacity': '0.2'
    })

    for child in list(root):
        root.remove(child)
        wrapper.append(child)
        clean_element(child) # Чистим детей
    root.append(wrapper)

    # 4. Финализация корня
    root.set('viewBox', '0 0 1000 1000')
    clean_element(root)

    return final_name, ET.tostring(root, encoding='unicode')


def main():
    parser = argparse.ArgumentParser(description="SVG Reference Extractor")
    parser.add_argument("input", help="Path to input file")
    parser.add_argument("-o", "--output", default="src/reference", help="Output directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"File not found: {args.input}")
        sys.exit(1)

    content = input_path.read_text()

    # Регулярка для поиска всех <svg ... </svg> (включая многострочные)
    svg_blocks = re.findall(r'<svg.*?</svg>', content, re.DOTALL)

    print(f"Found {len(svg_blocks)} SVG blocks. Processing...")

    name_registry = {}

    for i, svg_str in enumerate(svg_blocks, 1):
        result = process_svg(name_registry, svg_str, i)
        if result:
            name, clean_content = result
            file_path = output_dir / f"{name}.svg"
            file_path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + clean_content)
            print(f"  [OK] {file_path}")


if __name__ == "__main__":
    main()
