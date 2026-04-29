import logging
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import tomllib
import ufoLib2
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import SVGPath


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=level,
        stream=sys.stderr,
    )
    # INFO goes to stdout, WARNING and above go to stderr
    root = logging.getLogger()
    root.handlers.clear()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda r: r.levelno < logging.WARNING)
    stdout_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    root.setLevel(level)
    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)


def get_svg_width(svg_file: Path) -> float:
    tree = ET.parse(svg_file)
    root = tree.getroot()
    # Сначала ищем viewBox (это надежнее)
    viewbox = root.get('viewBox')
    if viewbox:
        return float(viewbox.split()[2])
    # Если viewBox нет, берем атрибут width
    return float(root.get('width', '1000').replace('px', ''))


def parse_svg_path(svg_file: Path) -> str:
    """
    Ищет слой (группу) с названием 'glyph' (inkscape:label).
    Если находит, извлекает контуры только из него.
    Если слоя нет, падает в fallback и ищет по всему файлу.
    """
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Ключи для пространств имен Inkscape для поиска лейблов
    NS = {
        'svg': 'http://www.w3.org/2000/svg',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
    }

    # 1. Ищем слой glyph. Используем xpath поиск групп <svg:g>
    # который имеют атрибут inkscape:label="glyph"
    glyph_layer = root.find(".//svg:g[@inkscape:label='glyph']", NS)

    if glyph_layer is None:
        # Если слой не найден, это критично для структуры
        logging.error("%s: layer with inkscape:label='glyph' not found", svg_file.name)
        return ""

    # 2. Собираем пути ТОЛЬКО внутри найденного слоя
    paths = []
    for path in glyph_layer.findall(".//svg:path", NS):
        d = path.get('d')
        if d:
            # Если у пути ID 'main_path', возвращаем его сразу (приоритет)
            if path.get('id') == 'main_path':
                return d
            paths.append(d)

    # Fallback: склеиваем все найденные контуры в один составной (compound path)
    return " ".join(paths)


def build_notdef(font, metrics):
    g = font.newGlyph(".notdef")

    asc  = metrics["ascender"]           # 1020
    desc = metrics["descender"]          # -300
    w    = metrics["advance_width_base"] # 800

    g.width = w

    margin  = 50   # боковой отступ рамки
    stroke  = 80   # толщина рамки = основной штрих из spec

    pen = g.getPen()
    # Внешний контур (по часовой)
    pen.moveTo((margin, desc))
    pen.lineTo((w - margin, desc))
    pen.lineTo((w - margin, asc))
    pen.lineTo((margin, asc))
    pen.closePath()
    # Внутренний контур (против часовой — дыра)
    pen.moveTo((margin + stroke, desc + stroke))
    pen.lineTo((margin + stroke, asc - stroke))
    pen.lineTo((w - margin - stroke, asc - stroke))
    pen.lineTo((w - margin - stroke, desc + stroke))
    pen.closePath()


def main() -> None:
    # Проверяем наличие ключей в аргументах запуска
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    setup_logging(verbose)

    # 1. Загрузка конфигурации из Single Source of Truth
    config_path = Path("src/config.toml")

    if not config_path.exists():
        logging.error("config file not found: %s", config_path)
        sys.exit(1)  # Выход с кодом ошибки

    with open(config_path, "rb") as f:
        try:
            config = tomllib.load(f)
        except Exception as e:
            print(f"❌ Ошибка парсинга {config_path}: {e}")
            sys.exit(1)

    logging.info("loaded config: %s", config_path)

    # 2. Подготовка директорий
    Path("build").mkdir(exist_ok=True)
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    ufo_path = Path("build/AstroPanMono.ufo")

    # 3. Инициализация объекта UFO
    font = ufoLib2.Font()

    font_cfg = config["font"]
    m = config["metrics"]

    # --- Конфигурация шрифта -----------

    # Авторские права
    font.info.familyName = font_cfg["family_name"]
    font.info.copyright = font_cfg.get("copyright", "")
    font.info.openTypeNameDesigner = font_cfg.get("designer", "")
    font.info.openTypeNameDesignerURL = font_cfg.get("designer_url", "")
    version_parts = str(font_cfg["version"]).split(".")
    font.info.versionMajor = int(version_parts[0])
    font.info.versionMinor = int(version_parts[1]) if len(version_parts) > 1 else 0
    font.info.openTypeNameLicense = font_cfg["license"]
    font.info.openTypeNameLicenseURL = font_cfg["license_url"]

    # Встраиваемость (fsType)
    # "Installable Embedding" (нет ограничений)
    font.info.openTypeOS2Type = []

    # Основные метрики UFO
    font.info.unitsPerEm = m["upm"]
    ascender = m["ascender"]
    descender = m["descender"]
    font.info.ascender = ascender
    font.info.descender = descender
    font.info.capHeight = m["cap_height"]
    font.info.xHeight = m["x_height"]

    # OS/2 (Windows) и hhea (macOS) метрики
    font.info.openTypeOS2TypoAscender = ascender
    font.info.openTypeOS2TypoDescender = descender
    line_gap = m["line_gap"]
    font.info.openTypeOS2TypoLineGap = line_gap

    font.info.openTypeHheaAscender = ascender
    font.info.openTypeHheaDescender = descender
    font.info.openTypeHheaLineGap = line_gap

    font.info.openTypeOS2WinAscent = m["win_ascent"]
    font.info.openTypeOS2WinDescent = m["win_descent"]

    # Чекбокс "Really use Typo metrics"
    # Bit 7 (значение 128) включает флаг USE_TYPO_METRICS
    font.info.openTypeOS2Selection = [7]

    # PFM Family (Windows Panose/Family)
    # В UFO это поле называется openTypeOS2FamilyClass
    font.info.openTypeOS2FamilyClass = [0, 0]

    # Дополнительные важные поля для Windows
    font.info.openTypeOS2VendorID = font_cfg.get("vendor", "")
    # Panose: 2=Latin, 11=Constant/Hidden, 5=Medium, 9=Monospaced, 2=None...
    # Четвертый элемент (9) критичен для Mono
    font.info.openTypeOS2Panose = [2, 11, 5, 9, 2, 2, 3, 2, 2, 4] # Стандарт для Mono

    # Моноширинный флаг для PostScript
    font.info.postscriptIsFixedPitch = font_cfg.get("is_fixed_pitch", False)

    # Индексы: Subscript (Нижние)
    font.info.openTypeOS2SubscriptYSize = m["sub_size_y"]
    font.info.openTypeOS2SubscriptYOffset = m["sub_offset_y"]

    # Индексы: Superscript (Верхние)
    font.info.openTypeOS2SuperscriptYSize = m["super_size_y"]
    font.info.openTypeOS2SuperscriptYOffset = m["super_offset_y"]

    # Подчеркивание
    font.info.postscriptUnderlinePosition = m["underline_position"]
    font.info.postscriptUnderlineThickness = m["underline_thickness"]

    # Зачеркивание
    font.info.openTypeOS2StrikeoutPosition = m["strikeout_position"]
    font.info.openTypeOS2StrikeoutSize = m["strikeout_size"]

    # Асцендер на SVG‐холсте
    canvas_ascender = m["ascender_upm"]

    # -----------------------------------

    advance_width_base = m["advance_width_base"]

    # Обязательный системный глиф .notdef
    build_notdef(font, m)

    # Глифы пробела (U+0020)
    space = font.newGlyph("space")
    space.unicode = 0x0020
    space.width = advance_width_base

    # Глиф неразрывного пробела (Non-Breaking Space) (U+00A0)
    nbsp = font.newGlyph("nbsp")
    nbsp.unicode = 0x00A0
    nbsp.width = advance_width_base

    # 4. Обработка глифов
    glyphs_dir = Path("src/glyphs")
    processed = skipped = failed = 0

    missing = []

    for name, unicode_str in config["glyphs"].items():
        svg_path = glyphs_dir / f"{name}.svg"

        if not svg_path.exists():
            missing.append(name)
            skipped += 1
            continue

        codepoint = int(unicode_str.replace("U+", ""), 16)

        # Получаем ширину глифа: ищем в переопределениях, иначе берем базовую
        target_width = config.get("glyph_widths", {}).get(name, advance_width_base)

        # Создаем глиф в UFO
        glyph = font.newGlyph(name)
        glyph.unicode = codepoint
        glyph.width = target_width

        # Парсинг SVG
        d_string = parse_svg_path(svg_path)
        if not d_string or d_string.strip() == "":
            logging.warning("glyph '%s': no path data found in '%s', skipping", name, svg_path.name)
            skipped += 1
            continue

        # --- БЛОК ДИАГНОСТИКИ (Verbose mode) ---
        if verbose:
            # Разрезаем строку на отдельные суб-контуры (по букве M/m)
            sub_paths = [p.strip() for p in d_string.replace('m', 'M').split('M') if p.strip()]
            logging.debug("glyph '%s': %d subpath(s) found", name, len(sub_paths))

            for i, sub in enumerate(sub_paths):
                is_closed = 'z' in sub.lower()
                status = "closed" if is_closed else "OPEN (error)"
                logging.debug("  subpath [%d]: %s -- %s...", i, status, sub[:50])
        # ---------------------------------------

        # 5. Трансформация координат (Inkscape -> Font)

        # Получаем реальную ширину холста из файла
        canvas_width = get_svg_width(svg_path)

        # Вычисляем dx для центровки
        # Формула: сдвигаем контур так, чтобы центр холста совпал с центром площадки глифа
        dx = (target_width / 2) - (canvas_width / 2)

        # Матрица трансформации (xx, xy, yx, yy, dx, dy)
        # (инверсия Y + центровка X)
        # Формула: y_font = ascender - y_inkscape
        # Соответствует: x' = 1*x + 0, y' = -1*y + ascender
        transformation = (1, 0, 0, -1, dx, canvas_ascender)

        # Отрисовка данных в геометрию глифа
        pen = glyph.getPen()
        transform_pen = TransformPen(pen, transformation)

        try:
            # Оборачиваем строку координат в XML-тег path для парсера
            wrapped_d = f'<path d="{d_string}"/>'
            svg_path_obj = SVGPath.fromstring(wrapped_d)
            svg_path_obj.draw(transform_pen)
        except Exception as exc:
            logging.error("glyph '%s': failed to draw contour: %s", name, exc)
            failed += 1
            continue

        logging.debug("glyph '%s': ok (U+%04X, width=%d)", name, codepoint, target_width)
        processed += 1

    if missing:
        if verbose:
            for name in missing:
                logging.warning("glyph '%s': source file not found, skipping", name)
        else:
            logging.warning(
                "%d glyph source file(s) not found, skipped"
                " (run with -v to list)", len(missing)
            )

    logging.info(
        "glyphs processed: %d, skipped: %d, failed: %d",
        processed, skipped, failed,
    )

    if failed > 0:
        logging.warning("%d glyph(s) failed to compile and were omitted", failed)

    # 6. Сохранение промежуточного формата
    font.save(ufo_path, overwrite=True)
    logging.info("UFO written: %s", ufo_path)

    # 7. Компиляция TTF (fontmake сам переведет кубические кривые Безье в квадратичные)
    font_name = config["output"]["font_name"]
    ttf_path = dist_dir / f"{font_name}.ttf"
    logging.info("compiling TTF via fontmake...")

    try:
        subprocess.run(
            ["fontmake", "-u", str(ufo_path), "-o", "ttf", "--output-path", str(ttf_path)],
            check=True,
            capture_output=True,  # Добавили захват вывода
            text=True
        )
    except subprocess.CalledProcessError as exc:
        logging.error("fontmake failed:")
        # Извлекаем только важные строки (ERROR и финальное сообщение)
        error_lines = [
            line for line in exc.stderr.split("\n")
            if any(tag in line for tag in ("ERROR", "failed:", "Error:"))
        ]
        for line in (error_lines or exc.stderr.splitlines()):
            logging.error("  %s", line)
        sys.exit(1)

    logging.info("TTF written: %s", ttf_path)

    # 7.1. Исправление хинтинга через gftools
    logging.info("fixing non-hinting with gftools...")
    try:
        subprocess.run([
            "gftools", "fix-nonhinting",
            str(ttf_path), str(ttf_path)
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        logging.error("gftools fix-nonhinting failed (exit code %d)", exc.returncode)
        sys.exit(1)

    backup_path = ttf_path.parent / (ttf_path.stem + "-backup-fonttools-prep-gasp.ttf")
    if backup_path.exists():
        backup_path.unlink()

    # 8. Сжатие в WOFF2 для веба
    woff2_path = dist_dir / f"{font_name}.woff2"
    logging.info("compressing to WOFF2 via pyftsubset...")

    try:
        subprocess.run(
            [
                "pyftsubset",
                str(ttf_path),
                "--flavor=woff2",
                "--output-file=" + str(woff2_path),
                "--unicodes=*"
            ],
            check=True
        )
    except subprocess.CalledProcessError as exc:
        logging.error("pyftsubset failed (exit code %d)", exc.returncode)
        sys.exit(1)

    logging.info("WOFF2 written: %s", woff2_path)

    # --- Summary ---
    print()
    print("build complete.")
    print(f"  {ttf_path}")
    print(f"  {woff2_path}")


if __name__ == "__main__":
    main()
