from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1080, 1350

BG = (7, 8, 9)
WHITE = (242, 239, 232)
MUTED = (183, 180, 172)
ACCENT = (216, 115, 50)
ACCENT_LIGHT = (239, 157, 91)
LINE = (107, 68, 43)
PANEL = (7, 9, 10, 236)

DISPLAY_PATH = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
BODY_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
BODY_BOLD_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def fit_scene(path):
    image = Image.open(path).convert("RGB")
    target_ratio = W / H
    ratio = image.width / image.height
    if ratio > target_ratio:
        new_width = int(image.height * target_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))
    else:
        new_height = int(image.width / target_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))
    return image.resize((W, H), Image.Resampling.LANCZOS)


def darken_scene(image, top_strength=225, bottom_strength=155):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(H):
        if y < 565:
            alpha = int(top_strength * (1 - y / 660) ** 1.55)
        elif y > 1020:
            alpha = int(bottom_strength * ((y - 970) / 380) ** 1.22)
        else:
            alpha = 9
        for x in range(W):
            edge = int(42 * (abs(x - W / 2) / (W / 2)) ** 2)
            pixels[x, y] = (2, 3, 3, min(235, alpha + edge))
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def make_canvas(index, top=225, bottom=155):
    image = fit_scene(ROOT / "scenes" / f"{index:02d}.png")
    image = ImageEnhance.Contrast(image).enhance(1.05)
    image = ImageEnhance.Color(image).enhance(0.86)
    return darken_scene(image, top, bottom)


def text_width(draw, value, face):
    box = draw.textbbox((0, 0), value, font=face)
    return box[2] - box[0]


def fit_font(draw, value, path, max_size, min_size, max_width):
    for size in range(max_size, min_size - 1, -1):
        face = font(path, size)
        if text_width(draw, value, face) <= max_width:
            return face
    return font(path, min_size)


def draw_border(draw):
    draw.rounded_rectangle((35, 35, W - 35, H - 35), radius=8, outline=LINE, width=2)


def draw_header(draw, index):
    face = font(BODY_BOLD_PATH, 19)
    draw.ellipse((74, 70, 85, 81), fill=ACCENT)
    draw.text((96, 65), "ТОВАР • ОСТАТКИ", font=face, fill=MUTED)
    value = f"{index:02d} / 07"
    draw.text((1006 - text_width(draw, value, face), 65), value, font=face, fill=MUTED)


def draw_brand(draw, source=None):
    face = font(BODY_PATH, 17)
    draw.text((74, 1280), "@hasbulla_gubdenskiy", font=face, fill=(150, 147, 140))
    if source:
        small = font(BODY_PATH, 14)
        draw.text((1006 - text_width(draw, source, small), 1281), source, font=small, fill=(137, 134, 128))


def panel(draw, box, radius=16, fill=PANEL, outline=(123, 82, 52, 225), width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, box, value, face, color=WHITE, gap=4):
    x1, y1, x2, y2 = box
    lines = value.split("\n")
    metrics = []
    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=face)
        metrics.append((bounds[2] - bounds[0], bounds[3] - bounds[1]))
    total_height = sum(height for _, height in metrics) + gap * (len(lines) - 1)
    y = y1 + (y2 - y1 - total_height) / 2
    for line, (width, height) in zip(lines, metrics):
        draw.text((x1 + (x2 - x1 - width) / 2, y), line, font=face, fill=color)
        y += height + gap


def headline(draw, lines, y=158, accent_lines=(), max_size=82, min_size=50, max_width=828, x=126, line_gap=1):
    sizes = [fit_font(draw, line, DISPLAY_PATH, max_size, min_size, max_width).size for line in lines]
    face = font(DISPLAY_PATH, min(sizes))
    line_height = int(face.size * 0.91)
    for index, line in enumerate(lines):
        color = ACCENT_LIGHT if index in accent_lines else WHITE
        draw.text((x, y + index * (line_height + line_gap)), line, font=face, fill=color)
    return y + len(lines) * (line_height + line_gap)


def bottom_statement(draw, value, y=1070, height=138, accent_line=None, max_size=30):
    box = (74, y, 1006, y + height)
    panel(draw, box, fill=(7, 9, 10, 239))
    lines = value.split("\n")
    face = fit_font(draw, max(lines, key=len), BODY_BOLD_PATH, max_size, 21, 830)
    if accent_line is None:
        center_text(draw, box, value, face, WHITE, 7)
        return
    line_height = max(33, int(face.size * 1.28))
    start_y = y + (height - line_height * len(lines)) / 2
    for index, line in enumerate(lines):
        color = ACCENT_LIGHT if index == accent_line else WHITE
        width = text_width(draw, line, face)
        draw.text(((W - width) / 2, start_y + index * line_height), line, font=face, fill=color)


def label_panel(draw, box, main, sub=None, accent=False, main_size=56):
    panel(draw, box, radius=16, fill=(6, 8, 9, 234), outline=(174, 99, 55, 225))
    main_face = fit_font(draw, main, DISPLAY_PATH, main_size, 36, box[2] - box[0] - 30)
    if sub:
        center_text(draw, (box[0] + 8, box[1] + 4, box[2] - 8, box[1] + 70), main, main_face, ACCENT_LIGHT if accent else WHITE)
        sub_face = fit_font(draw, max(sub.split("\n"), key=len), BODY_BOLD_PATH, 21, 17, box[2] - box[0] - 30)
        center_text(draw, (box[0] + 12, box[1] + 64, box[2] - 12, box[3] - 8), sub, sub_face, WHITE, 2)
    else:
        center_text(draw, box, main, main_face, ACCENT_LIGHT if accent else WHITE)


def save(image, index):
    image.convert("RGB").save(ROOT / f"{index:02d}.jpg", "JPEG", quality=95, optimize=True, progressive=True)


def slide_01():
    image = make_canvas(1, 236, 150)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 1)
    headline(draw, ["100 ЕДИНИЦ", "ТОВАРА.", "ЭТО МНОГО", "ИЛИ МАЛО?"], y=150, accent_lines=(0, 3), max_size=88)
    panel(draw, (126, 515, 610, 585), radius=13, fill=(7, 9, 10, 226))
    center_text(draw, (142, 523, 594, 577), "ОДНОГО ЧИСЛА НЕДОСТАТОЧНО", font(BODY_BOLD_PATH, 22), MUTED)
    draw.rounded_rectangle((126, 608, 286, 616), radius=4, fill=ACCENT)
    draw_brand(draw)
    save(image, 1)


def slide_02():
    image = make_canvas(2, 230, 170)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 2)
    headline(draw, ["100 ЕДИНИЦ", "ПРОДАЮТСЯ ПО", "10 В ДЕНЬ"], y=154, accent_lines=(2,), max_size=83)
    label_panel(draw, (666, 628, 995, 806), "≈ 10 ДНЕЙ", "ХВАТИТ ЗАПАСА", accent=True, main_size=59)
    bottom_statement(draw, "ЗАПАС МОЖЕТ ЗАКОНЧИТЬСЯ\nРАНЬШЕ НОВОЙ ПОСТАВКИ.", y=1068, height=140, accent_line=1, max_size=28)
    draw_brand(draw, "ПРИМЕР РАСЧЁТА")
    save(image, 2)


def slide_03():
    image = make_canvas(3, 230, 170)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 3)
    headline(draw, ["ТЕ ЖЕ 100 ЕДИНИЦ", "ПРОДАЮТСЯ", "ПО ОДНОЙ В ДЕНЬ"], y=154, accent_lines=(2,), max_size=79)
    label_panel(draw, (650, 650, 1000, 830), "≈ 100 ДНЕЙ", "ХВАТИТ ЗАПАСА", accent=True, main_size=57)
    bottom_statement(draw, "ПЕРЕД НОВОЙ ЗАКУПКОЙ ПРОВЕРЬТЕ,\nНУЖНО ЛИ ПОПОЛНЕНИЕ.", y=1068, height=140, accent_line=1, max_size=28)
    draw_brand(draw, "ПРИМЕР РАСЧЁТА")
    save(image, 3)


def slide_04():
    image = make_canvas(4, 230, 180)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 4)
    headline(draw, ["ПОСЧИТАЙТЕ", "ДНИ ЗАПАСА"], y=158, accent_lines=(1,), max_size=91)
    boxes = [
        ((52, 713, 329, 865), "ОСТАТОК", "100 ШТ."),
        ((402, 713, 679, 865), "ПРОДАЖИ В ДЕНЬ", "10 ШТ."),
        ((752, 713, 1029, 865), "ДНИ ЗАПАСА", "≈ 10"),
    ]
    for i, (box, label, value) in enumerate(boxes):
        panel(draw, box, radius=15, fill=(6, 8, 9, 236), outline=(177, 101, 56, 225))
        center_text(draw, (box[0] + 8, box[1] + 9, box[2] - 8, box[1] + 64), label, fit_font(draw, label, BODY_BOLD_PATH, 20, 16, box[2]-box[0]-22), MUTED)
        center_text(draw, (box[0] + 8, box[1] + 55, box[2] - 8, box[3] - 9), value, font(DISPLAY_PATH, 55), ACCENT_LIGHT if i == 2 else WHITE)
    sign_face = font(DISPLAY_PATH, 52)
    draw.text((348, 758), "÷", font=sign_face, fill=ACCENT_LIGHT)
    draw.text((695, 758), "=", font=sign_face, fill=ACCENT_LIGHT)
    bottom_statement(draw, "ТАК ВЫ УВИДИТЕ, НА СКОЛЬКО ДНЕЙ\nХВАТИТ ЗАПАСА.", y=1068, height=140, accent_line=1, max_size=28)
    draw_brand(draw, "МЕТОД: ORACLE / SAP")
    save(image, 4)


def slide_05():
    image = make_canvas(5, 232, 180)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 5)
    headline(draw, ["МАРКЕТПЛЕЙСЫ", "СМОТРЯТ НЕ ТОЛЬКО", "НА ШТУКИ"], y=150, accent_lines=(2,), max_size=75)
    panel(draw, (107, 760, 485, 865), radius=14, fill=(6, 8, 9, 232), outline=(173, 98, 54, 225))
    panel(draw, (595, 760, 973, 865), radius=14, fill=(6, 8, 9, 232), outline=(173, 98, 54, 225))
    center_text(draw, (107, 760, 485, 865), "WILDBERRIES\nОБОРАЧИВАЕМОСТЬ В ДНЯХ", font(BODY_BOLD_PATH, 21), WHITE, 4)
    center_text(draw, (595, 760, 973, 865), "ЯНДЕКС МАРКЕТ\nОБОРАЧИВАЕМОСТЬ В ДНЯХ", font(BODY_BOLD_PATH, 21), WHITE, 4)
    bottom_statement(draw, "ОНИ ОЦЕНИВАЮТ, ЗА СКОЛЬКО ДНЕЙ\nПРОДАСТСЯ ЗАПАС.", y=1068, height=140, accent_line=1, max_size=27)
    draw_brand(draw, "ИСТОЧНИКИ ПРОВЕРЕНЫ 13.08.2026")
    save(image, 5)


def slide_06():
    image = make_canvas(6, 232, 185)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 6)
    headline(draw, ["ДНИ ЗАПАСА", "ПОДСКАЗЫВАЮТ,", "ЧТО ПРОВЕРИТЬ"], y=150, accent_lines=(0,), max_size=74)
    cards = [
        ((34, 744, 347, 900), "МАЛО ДНЕЙ", "УСПЕЕТ ЛИ\nПОСТАВКА?"),
        ((384, 744, 697, 900), "РАБОЧИЙ ЗАПАС", "НУЖНО ЛИ\nМЕНЯТЬ ПЛАН?"),
        ((734, 744, 1047, 900), "СЛИШКОМ МНОГО", "СТОИТ ЛИ\nПОПОЛНЯТЬ?"),
    ]
    for i, (box, title, question) in enumerate(cards):
        panel(draw, box, radius=15, fill=(6, 8, 9, 238), outline=(177, 101, 56, 225))
        center_text(draw, (box[0]+8, box[1]+5, box[2]-8, box[1]+66), title, fit_font(draw, title, BODY_BOLD_PATH, 21, 17, box[2]-box[0]-30), ACCENT_LIGHT if i != 1 else WHITE)
        center_text(draw, (box[0]+14, box[1]+61, box[2]-14, box[3]-8), question, font(BODY_BOLD_PATH, 21), WHITE, 2)
    bottom_statement(draw, "УНИВЕРСАЛЬНОЙ НОРМЫ НЕТ.\nСВЕРЯЙТЕ СРОК ПОСТАВКИ И СПРОС.", y=1068, height=140, accent_line=1, max_size=26)
    draw_brand(draw)
    save(image, 6)


def numbered_item(draw, box, number, value):
    panel(draw, box, radius=14, fill=(6, 8, 9, 236), outline=(173, 98, 54, 225))
    draw.ellipse((box[0] + 15, box[1] + 18, box[0] + 51, box[1] + 54), fill=ACCENT)
    num_face = font(BODY_BOLD_PATH, 20)
    num_width = text_width(draw, str(number), num_face)
    draw.text((box[0] + 33 - num_width / 2, box[1] + 22), str(number), font=num_face, fill=WHITE)
    value_face = fit_font(draw, max(value.split("\n"), key=len), BODY_BOLD_PATH, 22, 17, box[2] - box[0] - 80)
    center_text(draw, (box[0] + 61, box[1] + 3, box[2] - 10, box[3] - 3), value, value_face, WHITE, 2)


def slide_07():
    image = make_canvas(7, 230, 190)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 7)
    headline(draw, ["РАЗ В НЕДЕЛЮ", "СМОТРИТЕ", "4 ЦИФРЫ"], y=150, accent_lines=(2,), max_size=87)
    numbered_item(draw, (91, 650, 511, 757), 1, "ОСТАТОК\nВ ШТУКАХ")
    numbered_item(draw, (569, 650, 989, 757), 2, "ПРОДАЖИ\nВ ДЕНЬ")
    numbered_item(draw, (91, 787, 511, 894), 3, "ДНИ\nЗАПАСА")
    numbered_item(draw, (569, 787, 989, 894), 4, "СРОК\nПОСТАВКИ")
    bottom_statement(draw, "ОТПРАВЬТЕ ТОМУ, КТО\nОТВЕЧАЕТ ЗА ЗАКУПКИ.", y=1068, height=140, accent_line=1, max_size=30)
    draw_brand(draw, "НАЧНИТЕ С КЛЮЧЕВЫХ ТОВАРОВ")
    save(image, 7)


def contact_sheet():
    thumb_w, thumb_h = 270, 338
    gap, margin = 34, 44
    columns, rows = 4, 2
    canvas = Image.new("RGB", (margin * 2 + columns * thumb_w + (columns - 1) * gap,
                               margin * 2 + rows * thumb_h + (rows - 1) * gap), BG)
    for index in range(1, 8):
        image = Image.open(ROOT / f"{index:02d}.jpg").convert("RGB")
        image = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = margin + ((index - 1) % columns) * (thumb_w + gap)
        y = margin + ((index - 1) // columns) * (thumb_h + gap)
        canvas.paste(image, (x, y))
    canvas.save(ROOT / "contact_sheet.jpg", "JPEG", quality=94, optimize=True)


def preview_safe_sheet():
    square = 270
    gap, margin = 34, 44
    columns, rows = 4, 2
    canvas = Image.new("RGB", (margin * 2 + columns * square + (columns - 1) * gap,
                               margin * 2 + rows * square + (rows - 1) * gap), BG)
    for index in range(1, 8):
        image = Image.open(ROOT / f"{index:02d}.jpg").convert("RGB")
        top = (H - W) // 2
        image = image.crop((0, top, W, top + W)).resize((square, square), Image.Resampling.LANCZOS)
        x = margin + ((index - 1) % columns) * (square + gap)
        y = margin + ((index - 1) // columns) * (square + gap)
        canvas.paste(image, (x, y))
    canvas.save(ROOT / "preview_safe_sheet.jpg", "JPEG", quality=94, optimize=True)


if __name__ == "__main__":
    slide_01(); slide_02(); slide_03(); slide_04(); slide_05(); slide_06(); slide_07()
    contact_sheet(); preview_safe_sheet()
