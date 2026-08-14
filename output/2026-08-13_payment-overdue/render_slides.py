from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = Path(__file__).resolve().parent
W, H = 1080, 1350

BG = (7, 8, 9)
WHITE = (242, 239, 232)
MUTED = (183, 180, 172)
ACCENT = (216, 115, 50)
ACCENT_LIGHT = (239, 157, 91)
LINE = (107, 68, 43)
PANEL = (8, 10, 11, 235)

DISPLAY_PATH = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
BODY_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
BODY_BOLD_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def fit_scene(path):
    im = Image.open(path).convert("RGB")
    target_ratio = W / H
    ratio = im.width / im.height
    if ratio > target_ratio:
        new_width = int(im.height * target_ratio)
        left = (im.width - new_width) // 2
        im = im.crop((left, 0, left + new_width, im.height))
    else:
        new_height = int(im.width / target_ratio)
        top = (im.height - new_height) // 2
        im = im.crop((0, top, im.width, top + new_height))
    return im.resize((W, H), Image.Resampling.LANCZOS)


def darken_scene(im, top_strength=220, bottom_strength=155):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(H):
        if y < 560:
            alpha = int(top_strength * (1 - y / 650) ** 1.55)
        elif y > 1030:
            alpha = int(bottom_strength * ((y - 980) / 370) ** 1.25)
        else:
            alpha = 10
        for x in range(W):
            edge = int(45 * (abs(x - W / 2) / (W / 2)) ** 2)
            pixels[x, y] = (2, 3, 3, min(235, alpha + edge))
    return Image.alpha_composite(im.convert("RGBA"), overlay)


def make_canvas(index, top=220, bottom=155):
    im = fit_scene(ROOT / "scenes" / f"{index:02d}.png")
    im = ImageEnhance.Contrast(im).enhance(1.05)
    im = ImageEnhance.Color(im).enhance(0.88)
    return darken_scene(im, top, bottom)


def text_width(draw, value, f):
    box = draw.textbbox((0, 0), value, font=f)
    return box[2] - box[0]


def fit_font(draw, value, path, max_size, min_size, max_width):
    for size in range(max_size, min_size - 1, -1):
        f = font(path, size)
        if text_width(draw, value, f) <= max_width:
            return f
    return font(path, min_size)


def draw_border(draw):
    draw.rounded_rectangle((35, 35, W - 35, H - 35), radius=8, outline=LINE, width=2)


def draw_header(draw, index):
    f = font(BODY_BOLD_PATH, 19)
    draw.ellipse((74, 70, 85, 81), fill=ACCENT)
    draw.text((96, 65), "ФИНАНСЫ • ПРОДАЖИ", font=f, fill=MUTED)
    value = f"{index:02d} / 07"
    draw.text((1006 - text_width(draw, value, f), 65), value, font=f, fill=MUTED)


def draw_brand(draw, source=None):
    f = font(BODY_PATH, 17)
    draw.text((74, 1280), "@hasbulla_gubdenskiy", font=f, fill=(150, 147, 140))
    if source:
        sf = font(BODY_PATH, 15)
        draw.text((1006 - text_width(draw, source, sf), 1281), source, font=sf, fill=(137, 134, 128))


def panel(draw, box, radius=16, fill=PANEL, outline=(123, 82, 52, 225), width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, box, value, f, color=WHITE, gap=4):
    x1, y1, x2, y2 = box
    lines = value.split("\n")
    metrics = []
    for line in lines:
        b = draw.textbbox((0, 0), line, font=f)
        metrics.append((b[2] - b[0], b[3] - b[1]))
    total_height = sum(h for _, h in metrics) + gap * (len(lines) - 1)
    y = y1 + (y2 - y1 - total_height) / 2
    for line, (width, height) in zip(lines, metrics):
        draw.text((x1 + (x2 - x1 - width) / 2, y), line, font=f, fill=color)
        y += height + gap


def headline(draw, lines, y=155, accent_lines=(), max_size=82, min_size=52, max_width=828, x=126, line_gap=1):
    sizes = []
    for line in lines:
        sizes.append(fit_font(draw, line, DISPLAY_PATH, max_size, min_size, max_width).size)
    f = font(DISPLAY_PATH, min(sizes))
    line_height = int(f.size * 0.91)
    for index, line in enumerate(lines):
        color = ACCENT_LIGHT if index in accent_lines else WHITE
        draw.text((x, y + index * (line_height + line_gap)), line, font=f, fill=color)
    return y + len(lines) * (line_height + line_gap)


def bottom_statement(draw, value, y=1090, height=120, accent_line=None, max_size=30):
    box = (74, y, 1006, y + height)
    panel(draw, box, fill=(7, 9, 10, 238))
    lines = value.split("\n")
    f = fit_font(draw, max(lines, key=len), BODY_BOLD_PATH, max_size, 23, 830)
    if accent_line is None:
        center_text(draw, box, value, f, WHITE, 7)
    else:
        line_height = 38
        start_y = y + (height - line_height * len(lines)) / 2
        for idx, line in enumerate(lines):
            color = ACCENT_LIGHT if idx == accent_line else WHITE
            width = text_width(draw, line, f)
            draw.text(((W - width) / 2, start_y + idx * line_height), line, font=f, fill=color)


def save(im, index):
    im.convert("RGB").save(ROOT / f"{index:02d}.jpg", "JPEG", quality=95, optimize=True, progressive=True)


def slide_01():
    im = make_canvas(1, 230, 130)
    draw = ImageDraw.Draw(im)
    draw_border(draw); draw_header(draw, 1)
    headline(draw, ["РАБОТА ВЫПОЛНЕНА.", "А ДЕНЕГ ДО СИХ", "ПОР НЕТ."], y=158, accent_lines=(1, 2), max_size=83)
    panel(draw, (126, 445, 662, 515), radius=13, fill=(7, 9, 10, 226))
    center_text(draw, (142, 453, 646, 507), "Где заканчивается продажа", font(BODY_BOLD_PATH, 25), MUTED)
    draw.rounded_rectangle((126, 542, 286, 550), radius=4, fill=ACCENT)
    draw_brand(draw)
    save(im, 1)


def slide_02():
    im = make_canvas(2, 225, 175)
    draw = ImageDraw.Draw(im)
    draw_border(draw); draw_header(draw, 2)
    headline(draw, ["СДЕЛКА ЗАКРЫТА.", "НО ПЛАТЁЖ ЕЩЁ", "НЕ ПРИШЁЛ."], y=158, accent_lines=(1, 2), max_size=79)
    left = (78, 795, 468, 884)
    right = (612, 795, 1002, 884)
    panel(draw, left, fill=(7, 9, 10, 231), outline=(105, 102, 95, 215))
    panel(draw, right, fill=(7, 9, 10, 231), outline=(183, 103, 57, 225))
    center_text(draw, left, "РАБОТА ВЫПОЛНЕНА", font(BODY_BOLD_PATH, 24), WHITE)
    center_text(draw, right, "ДЕНЬГИ ПРИШЛИ", font(BODY_BOLD_PATH, 24), ACCENT_LIGHT)
    bottom_statement(draw, "ЭТО ДВА РАЗНЫХ СОБЫТИЯ.", y=1090, height=116)
    draw_brand(draw)
    save(im, 2)


def slide_03():
    im = make_canvas(3, 225, 165)
    draw = ImageDraw.Draw(im)
    draw_border(draw); draw_header(draw, 3)
    headline(draw, ["237 ОБРАЩЕНИЙ", "О НЕПЛАТЕЖАХ"], y=158, accent_lines=(0,), max_size=86)
    number_box = (596, 555, 1005, 815)
    panel(draw, number_box, radius=18, fill=(5, 7, 8, 200), outline=(190, 109, 58, 230), width=3)
    center_text(draw, (610, 574, 990, 690), "1,6 МЛРД", font(DISPLAY_PATH, 73), ACCENT_LIGHT)
    center_text(draw, (610, 682, 990, 755), "РУБЛЕЙ", font(DISPLAY_PATH, 50), WHITE)
    center_text(draw, (610, 754, 990, 801), "общая сумма", font(BODY_PATH, 22), MUTED)
    bottom_statement(draw, "НЕПЛАТЕЖИ ГОСЗАКАЗЧИКОВ\nС НАЧАЛА 2026 ГОДА", y=1075, height=134, accent_line=1, max_size=27)
    draw_brand(draw, "ИСТОЧНИК: КОРПОРАЦИЯ МСП, 21.05.2026")
    save(im, 3)


def slide_04():
    im = make_canvas(4, 225, 165)
    draw = ImageDraw.Draw(im)
    draw_border(draw); draw_header(draw, 4)
    headline(draw, ["КЛИЕНТ ЕЩЁ", "НЕ ЗАПЛАТИЛ."], y=158, accent_lines=(1,), max_size=88)
    panel(draw, (78, 805, 428, 890), fill=(7, 9, 10, 228))
    center_text(draw, (90, 814, 416, 881), "ВАШИ РАСХОДЫ", font(BODY_BOLD_PATH, 25), WHITE)
    panel(draw, (687, 805, 1002, 890), fill=(7, 9, 10, 228), outline=(169, 94, 52, 225))
    center_text(draw, (699, 814, 990, 881), "КЛИЕНТ", font(BODY_BOLD_PATH, 25), ACCENT_LIGHT)
    bottom_statement(draw, "А ВЫ УЖЕ МОГЛИ ОПЛАТИТЬ\nЕГО ЗАКАЗ.", y=1075, height=134, accent_line=1)
    draw_brand(draw)
    save(im, 4)


def slide_05():
    im = make_canvas(5, 220, 180)
    draw = ImageDraw.Draw(im)
    draw_border(draw); draw_header(draw, 5)
    headline(draw, ["КОНТРОЛИРУЙТЕ", "3 ДАТЫ"], y=158, accent_lines=(1,), max_size=91)
    labels = [
        ((88, 588, 355, 680), "РАБОТА\nВЫПОЛНЕНА"),
        ((407, 588, 674, 680), "СРОК\nОПЛАТЫ"),
        ((726, 588, 993, 680), "ДЕНЬГИ\nПРИШЛИ"),
    ]
    for i, (box, value) in enumerate(labels, 1):
        panel(draw, box, radius=13, fill=(6, 8, 9, 231), outline=(175, 99, 55, 225))
        center_text(draw, box, value, font(BODY_BOLD_PATH, 23), ACCENT_LIGHT if i == 3 else WHITE, 3)
    bottom_statement(draw, "ТАК ВЫ СРАЗУ ВИДИТЕ\nПРОСРОЧЕННЫЕ ОПЛАТЫ.", y=1070, height=138, accent_line=1, max_size=28)
    draw_brand(draw)
    save(im, 5)


def slide_06():
    im = make_canvas(6, 225, 175)
    draw = ImageDraw.Draw(im)
    draw_border(draw); draw_header(draw, 6)
    headline(draw, ["ПРОСРОЧКА ДОЛЖНА", "СТАТЬ ЗАДАЧЕЙ", "В ПЕРВЫЙ ДЕНЬ."], y=158, accent_lines=(1, 2), max_size=76)
    labels = [
        ((75, 884, 355, 968), "ОТВЕТСТВЕННЫЙ"),
        ((400, 884, 680, 968), "СЛЕДУЮЩИЙ ШАГ"),
        ((725, 884, 1005, 968), "НОВЫЙ СРОК"),
    ]
    for index, (box, value) in enumerate(labels, 1):
        panel(draw, box, radius=13, fill=(6, 8, 9, 232), outline=(173, 98, 54, 225))
        draw.ellipse((box[0] + 13, box[1] + 27, box[0] + 42, box[1] + 56), fill=ACCENT)
        num_font = font(BODY_BOLD_PATH, 17)
        num = str(index)
        num_w = text_width(draw, num, num_font)
        draw.text((box[0] + 27.5 - num_w / 2, box[1] + 30), num, font=num_font, fill=WHITE)
        value_font = fit_font(draw, value, BODY_BOLD_PATH, 21, 17, 205)
        draw.text((box[0] + 54, box[1] + 32), value, font=value_font, fill=WHITE)
    bottom_statement(draw, "БЕЗ ЭТОГО ПРОСРОЧКА ПРОСТО СТАРЕЕТ.", y=1084, height=120, max_size=28)
    draw_brand(draw)
    save(im, 6)


def slide_07():
    im = make_canvas(7, 225, 190)
    draw = ImageDraw.Draw(im)
    draw_border(draw); draw_header(draw, 7)
    headline(draw, ["ПРОВЕРЬТЕ СЕГОДНЯ", "3 САМЫХ СТАРЫХ", "ДОЛГА КЛИЕНТОВ."], y=158, accent_lines=(1, 2), max_size=75)
    labels = [
        ((90, 824, 365, 905), "СУММА"),
        ((403, 824, 678, 905), "ОТВЕТСТВЕННЫЙ"),
        ((716, 824, 991, 905), "СЛЕДУЮЩИЙ ШАГ"),
    ]
    for box, value in labels:
        panel(draw, box, radius=13, fill=(6, 8, 9, 230), outline=(172, 97, 54, 225))
        value_font = fit_font(draw, value, BODY_BOLD_PATH, 23, 18, 225)
        center_text(draw, box, value, value_font, WHITE)
    bottom_statement(draw, "ЧТО ЧАЩЕ ЗАДЕРЖИВАЕТ ОПЛАТУ:\nДОКУМЕНТЫ, КЛИЕНТ ИЛИ КОНТРОЛЬ?", y=1068, height=140, accent_line=1, max_size=27)
    draw_brand(draw)
    save(im, 7)


def contact_sheet():
    thumb_w, thumb_h = 270, 338
    gap, margin = 34, 44
    columns, rows = 4, 2
    canvas = Image.new("RGB", (margin * 2 + columns * thumb_w + (columns - 1) * gap,
                               margin * 2 + rows * thumb_h + (rows - 1) * gap), BG)
    for index in range(1, 8):
        im = Image.open(ROOT / f"{index:02d}.jpg").convert("RGB")
        im = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = margin + ((index - 1) % columns) * (thumb_w + gap)
        y = margin + ((index - 1) // columns) * (thumb_h + gap)
        canvas.paste(im, (x, y))
    canvas.save(ROOT / "contact_sheet.jpg", "JPEG", quality=94, optimize=True)


def preview_safe_sheet():
    square = 270
    gap, margin = 34, 44
    columns, rows = 4, 2
    canvas = Image.new("RGB", (margin * 2 + columns * square + (columns - 1) * gap,
                               margin * 2 + rows * square + (rows - 1) * gap), BG)
    for index in range(1, 8):
        im = Image.open(ROOT / f"{index:02d}.jpg").convert("RGB")
        top = (H - W) // 2
        im = im.crop((0, top, W, top + W)).resize((square, square), Image.Resampling.LANCZOS)
        x = margin + ((index - 1) % columns) * (square + gap)
        y = margin + ((index - 1) // columns) * (square + gap)
        canvas.paste(im, (x, y))
    canvas.save(ROOT / "preview_safe_sheet.jpg", "JPEG", quality=94, optimize=True)


if __name__ == "__main__":
    slide_01(); slide_02(); slide_03(); slide_04(); slide_05(); slide_06(); slide_07()
    contact_sheet(); preview_safe_sheet()
