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
        if y < 570:
            alpha = int(top_strength * (1 - y / 660) ** 1.55)
        elif y > 1030:
            alpha = int(bottom_strength * ((y - 980) / 370) ** 1.25)
        else:
            alpha = 10
        for x in range(W):
            edge = int(44 * (abs(x - W / 2) / (W / 2)) ** 2)
            pixels[x, y] = (2, 3, 3, min(235, alpha + edge))
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def make_canvas(index, top=225, bottom=155):
    image = fit_scene(ROOT / "scenes" / f"{index:02d}.png")
    image = ImageEnhance.Contrast(image).enhance(1.05)
    image = ImageEnhance.Color(image).enhance(0.88)
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
    draw.text((96, 65), "КОМАНДА • НАЙМ", font=face, fill=MUTED)
    value = f"{index:02d} / 07"
    draw.text((1006 - text_width(draw, value, face), 65), value, font=face, fill=MUTED)


def draw_brand(draw, source=None):
    face = font(BODY_PATH, 17)
    draw.text((74, 1280), "@hasbulla_gubdenskiy", font=face, fill=(150, 147, 140))
    if source:
        small = font(BODY_PATH, 15)
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


def bottom_statement(draw, value, y=1085, height=120, accent_line=None, max_size=30):
    box = (74, y, 1006, y + height)
    panel(draw, box, fill=(7, 9, 10, 239))
    lines = value.split("\n")
    face = fit_font(draw, max(lines, key=len), BODY_BOLD_PATH, max_size, 22, 830)
    if accent_line is None:
        center_text(draw, box, value, face, WHITE, 7)
        return
    line_height = 38
    start_y = y + (height - line_height * len(lines)) / 2
    for index, line in enumerate(lines):
        color = ACCENT_LIGHT if index == accent_line else WHITE
        width = text_width(draw, line, face)
        draw.text(((W - width) / 2, start_y + index * line_height), line, font=face, fill=color)


def save(image, index):
    image.convert("RGB").save(ROOT / f"{index:02d}.jpg", "JPEG", quality=95, optimize=True, progressive=True)


def slide_01():
    image = make_canvas(1, 232, 135)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 1)
    headline(draw, ["ВЫ НАНЯЛИ", "СОТРУДНИКА.", "ЧТО ОН ДОЛЖЕН", "СДЕЛАТЬ К ПЯТНИЦЕ?"], y=152, accent_lines=(2, 3), max_size=74)
    panel(draw, (126, 505, 690, 575), radius=13, fill=(7, 9, 10, 226))
    center_text(draw, (142, 513, 674, 567), "Первый результат нового сотрудника", font(BODY_BOLD_PATH, 24), MUTED)
    draw.rounded_rectangle((126, 600, 286, 608), radius=4, fill=ACCENT)
    draw_brand(draw)
    save(image, 1)


def slide_02():
    image = make_canvas(2, 225, 170)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 2)
    headline(draw, ["НАЙМ ЗАНИМАЕТ", "25–30 ДНЕЙ"], y=158, accent_lines=(1,), max_size=89)
    data = [
        ((58, 730, 348, 923), "25", "ЛИНЕЙНЫЙ\nСПЕЦИАЛИСТ"),
        ((395, 730, 685, 923), "28", "РАБОЧИЙ"),
        ((732, 730, 1022, 923), "30", "РУКОВОДИТЕЛЬ"),
    ]
    for box, number, label in data:
        panel(draw, box, radius=18, fill=(6, 8, 9, 231), outline=(177, 101, 56, 225))
        center_text(draw, (box[0], box[1] + 13, box[2], box[1] + 115), number, font(DISPLAY_PATH, 73), ACCENT_LIGHT)
        center_text(draw, (box[0] + 12, box[1] + 109, box[2] - 12, box[3] - 12), label, font(BODY_BOLD_PATH, 21), WHITE, 2)
    bottom_statement(draw, "ПОСЛЕ ПОИСКА НЕ ТЕРЯЙТЕ\nПЕРВУЮ РАБОЧУЮ НЕДЕЛЮ.", y=1068, height=140, accent_line=1, max_size=28)
    draw_brand(draw, "ИСТОЧНИК: SUPERJOB, 23.03.2026")
    save(image, 2)


def slide_03():
    image = make_canvas(3, 225, 170)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 3)
    headline(draw, ["60% ХОТЕЛИ БЫ", "БЫСТРЕЕ ПОНЯТЬ,", "КАКИМИ ЗАДАЧАМИ", "ЗАНИМАТЬСЯ"], y=150, accent_lines=(0,), max_size=71)
    panel(draw, (607, 718, 930, 880), radius=17, fill=(7, 9, 10, 215), outline=(185, 106, 58, 225))
    center_text(draw, (619, 730, 918, 807), "ОДНА", font(DISPLAY_PATH, 58), ACCENT_LIGHT)
    center_text(draw, (619, 802, 918, 864), "ЯСНАЯ ЗАДАЧА", font(BODY_BOLD_PATH, 23), WHITE)
    bottom_statement(draw, "НОВИЧКУ НУЖНО ПОНЯТЬ,\nС ЧЕГО НАЧАТЬ.", y=1072, height=136, accent_line=1, max_size=28)
    draw_brand(draw, "ИСТОЧНИК: HH.RU, 12.08.2024")
    save(image, 3)


def slide_04():
    image = make_canvas(4, 226, 165)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 4)
    headline(draw, ["СПИСКА ЗАДАЧ", "НЕДОСТАТОЧНО."], y=158, accent_lines=(1,), max_size=86)
    left = (73, 813, 450, 900)
    right = (626, 813, 1003, 900)
    panel(draw, left, fill=(7, 9, 10, 231), outline=(105, 102, 95, 215))
    panel(draw, right, fill=(7, 9, 10, 231), outline=(183, 103, 57, 225))
    center_text(draw, left, "МНОГО ЗАДАЧ", font(BODY_BOLD_PATH, 24), MUTED)
    center_text(draw, right, "ОДИН РЕЗУЛЬТАТ", font(BODY_BOLD_PATH, 24), ACCENT_LIGHT)
    bottom_statement(draw, "НАЗОВИТЕ ОДИН\nПЕРВЫЙ РЕЗУЛЬТАТ.", y=1074, height=134, accent_line=1, max_size=31)
    draw_brand(draw)
    save(image, 4)


def slide_05():
    image = make_canvas(5, 224, 175)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 5)
    headline(draw, ["ПЕРВЫЙ РЕЗУЛЬТАТ", "ДОЛЖЕН БЫТЬ"], y=158, accent_lines=(1,), max_size=80)
    labels = [
        ((62, 760, 335, 858), "ПОЛЕЗЕН\nРАБОТЕ"),
        ((404, 760, 677, 858), "РЕАЛЕН\nЗА НЕДЕЛЮ"),
        ((746, 760, 1019, 858), "ЕГО МОЖНО\nПРОВЕРИТЬ"),
    ]
    for index, (box, value) in enumerate(labels, 1):
        panel(draw, box, radius=14, fill=(6, 8, 9, 232), outline=(173, 98, 54, 225))
        draw.ellipse((box[0] + 14, box[1] + 16, box[0] + 46, box[1] + 48), fill=ACCENT)
        number_face = font(BODY_BOLD_PATH, 18)
        number = str(index)
        number_width = text_width(draw, number, number_face)
        draw.text((box[0] + 30 - number_width / 2, box[1] + 20), number, font=number_face, fill=WHITE)
        center_text(draw, (box[0] + 49, box[1] + 5, box[2] - 7, box[3] - 5), value, font(BODY_BOLD_PATH, 21), WHITE, 2)
    bottom_statement(draw, "ЭТО НЕ ВСЯ РАБОТА.\nЭТО ПЕРВЫЙ ПОНЯТНЫЙ РЕЗУЛЬТАТ.", y=1070, height=138, accent_line=1, max_size=28)
    draw_brand(draw)
    save(image, 5)


def slide_06():
    image = make_canvas(6, 224, 175)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 6)
    headline(draw, ["ДАЙТЕ НОВИЧКУ", "3 ОПОРЫ"], y=158, accent_lines=(1,), max_size=91)
    labels = [
        ((55, 740, 347, 838), "ХОРОШИЙ\nПРИМЕР"),
        ((394, 740, 686, 838), "ЧЕЛОВЕК ДЛЯ\nВОПРОСОВ"),
        ((733, 740, 1025, 838), "ПРОВЕРКА\nВ ПЯТНИЦУ"),
    ]
    for box, value in labels:
        panel(draw, box, radius=14, fill=(6, 8, 9, 232), outline=(173, 98, 54, 225))
        center_text(draw, box, value, font(BODY_BOLD_PATH, 22), WHITE, 2)
    bottom_statement(draw, "ТАК НОВИЧОК ПОНИМАЕТ, КАК НАЧАТЬ\nИ ГДЕ СПРОСИТЬ.", y=1070, height=138, accent_line=1, max_size=28)
    draw_brand(draw)
    save(image, 6)


def numbered_item(draw, box, number, value):
    panel(draw, box, radius=14, fill=(6, 8, 9, 236), outline=(173, 98, 54, 225))
    draw.ellipse((box[0] + 15, box[1] + 18, box[0] + 51, box[1] + 54), fill=ACCENT)
    num_face = font(BODY_BOLD_PATH, 20)
    num_width = text_width(draw, str(number), num_face)
    draw.text((box[0] + 33 - num_width / 2, box[1] + 22), str(number), font=num_face, fill=WHITE)
    value_face = fit_font(draw, max(value.split("\n"), key=len), BODY_BOLD_PATH, 23, 18, box[2] - box[0] - 86)
    center_text(draw, (box[0] + 63, box[1] + 3, box[2] - 10, box[3] - 3), value, value_face, WHITE, 2)


def slide_07():
    image = make_canvas(7, 224, 185)
    draw = ImageDraw.Draw(image)
    draw_border(draw); draw_header(draw, 7)
    headline(draw, ["ДО ВЫХОДА НОВИЧКА", "ОТВЕТЬТЕ НА", "4 ВОПРОСА"], y=150, accent_lines=(2,), max_size=77)
    numbered_item(draw, (91, 654, 511, 761), 1, "ЧТО ОН\nСДЕЛАЕТ?")
    numbered_item(draw, (569, 654, 989, 761), 2, "К КАКОМУ\nДНЮ?")
    numbered_item(draw, (91, 791, 511, 898), 3, "ГДЕ ХОРОШИЙ\nПРИМЕР?")
    numbered_item(draw, (569, 791, 989, 898), 4, "КТО ПРОВЕРИТ?")
    bottom_statement(draw, "СОХРАНИТЕ ПЕРЕД\nСЛЕДУЮЩИМ НАЙМОМ.", y=1070, height=138, accent_line=1, max_size=29)
    draw_brand(draw)
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
