from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent
W, H = 1080, 1350

BG = (8, 9, 10)
PANEL = (10, 12, 13, 235)
WHITE = (239, 236, 228)
MUTED = (183, 181, 175)
ACCENT = (213, 111, 48)
ACCENT_LIGHT = (233, 150, 86)
LINE = (104, 67, 43)

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
        nw = int(im.height * target_ratio)
        left = (im.width - nw) // 2
        im = im.crop((left, 0, left + nw, im.height))
    else:
        nh = int(im.width / target_ratio)
        top = (im.height - nh) // 2
        im = im.crop((0, top, im.width, top + nh))
    return im.resize((W, H), Image.Resampling.LANCZOS)


def overlay_gradient(im, top_strength=205, bottom_strength=160):
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = shade.load()
    for y in range(H):
        if y < 520:
            a = int(top_strength * (1 - y / 620) ** 1.6)
        elif y > 1050:
            a = int(bottom_strength * ((y - 1000) / 350) ** 1.3)
        else:
            a = 12
        for x in range(W):
            edge = int(52 * (abs(x - W / 2) / (W / 2)) ** 2)
            px[x, y] = (2, 3, 3, min(235, a + edge))
    return Image.alpha_composite(im.convert("RGBA"), shade)


def draw_border(draw):
    draw.rounded_rectangle((34, 34, W - 34, H - 34), radius=8, outline=LINE, width=2)


def draw_header(draw, idx, category="УПРАВЛЕНИЕ • РЕШЕНИЯ"):
    f = font(BODY_BOLD_PATH, 19)
    draw.ellipse((74, 70, 85, 81), fill=ACCENT)
    draw.text((96, 65), category, font=f, fill=MUTED)
    draw.text((941, 65), f"{idx:02d} / 06", font=f, fill=MUTED)


def draw_brand(draw, source=False):
    f = font(BODY_PATH, 17)
    draw.text((74, 1280), "@hasbulla_gubdenskiy", font=f, fill=(151, 149, 143))
    if source:
        label = "ИСТОЧНИК: AMAZON, 2015 / 2024"
        bbox = draw.textbbox((0, 0), label, font=f)
        draw.text((1006 - (bbox[2] - bbox[0]), 1280), label, font=f, fill=(140, 138, 132))


def text_width(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def fit_font(draw, text, path, max_size, min_size, width):
    size = max_size
    while size > min_size:
        f = font(path, size)
        if text_width(draw, text, f) <= width:
            return f
        size -= 1
    return font(path, min_size)


def headline(draw, lines, y=118, accent_lines=(), max_size=86, min_size=54, width=930, line_gap=0):
    f = font(DISPLAY_PATH, max_size)
    for line in lines:
        if text_width(draw, line, f) > width:
            f = fit_font(draw, line, DISPLAY_PATH, max_size, min_size, width)
    line_h = int(f.size * 0.91)
    for i, line in enumerate(lines):
        color = ACCENT if i in accent_lines else WHITE
        draw.text((74, y + i * (line_h + line_gap)), line, font=f, fill=color)
    return y + len(lines) * (line_h + line_gap)


def panel(draw, box, radius=18, fill=PANEL, outline=(108, 74, 48, 230), width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, box, text, f, fill=WHITE, spacing=6):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    heights = []
    widths = []
    for line in lines:
        b = draw.textbbox((0, 0), line, font=f)
        widths.append(b[2] - b[0])
        heights.append(b[3] - b[1])
    total = sum(heights) + spacing * (len(lines) - 1)
    y = y1 + (y2 - y1 - total) / 2
    for line, tw, th in zip(lines, widths, heights):
        draw.text((x1 + (x2 - x1 - tw) / 2, y), line, font=f, fill=fill)
        y += th + spacing


def bottom_statement(draw, text, y=1110, h=118, accent_second=False):
    box = (74, y, 1006, y + h)
    panel(draw, box)
    lines = text.split("\n")
    f = fit_font(draw, max(lines, key=len), BODY_BOLD_PATH, 31, 24, 820)
    if accent_second and len(lines) == 2:
        center_text(draw, (box[0], box[1] + 12, box[2], box[1] + h // 2 + 14), lines[0], f, WHITE)
        center_text(draw, (box[0], box[1] + h // 2 - 4, box[2], box[3] - 10), lines[1], f, ACCENT_LIGHT)
    else:
        center_text(draw, box, text, f, WHITE, 8)


def make_canvas(index, top=205, bottom=160):
    scene = fit_scene(ROOT / "scenes" / f"{index:02d}.png")
    scene = ImageEnhance.Contrast(scene).enhance(1.06)
    scene = ImageEnhance.Color(scene).enhance(0.92)
    return overlay_gradient(scene, top, bottom)


def save_slide(im, index):
    out = ROOT / f"{index:02d}.jpg"
    im.convert("RGB").save(out, "JPEG", quality=95, optimize=True, progressive=True)


def slide1():
    im = make_canvas(1, 225, 150)
    d = ImageDraw.Draw(im)
    draw_border(d); draw_header(d, 1)
    headline(d, ["ЕСЛИ РЕШЕНИЕ", "МОЖНО ОТМЕНИТЬ —", "ЗАЧЕМ ОНО", "ДОШЛО ДО ВАС?"], y=120, accent_lines=(2, 3), max_size=82)
    panel(d, (74, 474, 684, 548), radius=13, fill=(9, 11, 12, 220))
    center_text(d, (92, 482, 666, 540), "Простой способ разделить решения\nсобственника и команды", font(BODY_BOLD_PATH, 25), MUTED, 5)
    d.rounded_rectangle((74, 566, 230, 574), radius=4, fill=ACCENT)
    draw_brand(d, source=True)
    save_slide(im, 1)


def slide2():
    im = make_canvas(2, 225, 180)
    d = ImageDraw.Draw(im)
    draw_border(d); draw_header(d, 2)
    headline(d, ["У КАЖДОГО РЕШЕНИЯ —", "СВОЯ ДВЕРЬ."], y=122, accent_lines=(1,), max_size=76)
    left = (74, 785, 497, 890); right = (583, 785, 1006, 890)
    panel(d, left, fill=(8, 10, 11, 235), outline=(112, 108, 101, 220))
    panel(d, right, fill=(8, 10, 11, 235), outline=(182, 101, 51, 235))
    center_text(d, left, "ТРУДНО ВЕРНУТЬСЯ", font(DISPLAY_PATH, 42), WHITE)
    center_text(d, right, "ЛЕГКО ВЕРНУТЬСЯ", font(DISPLAY_PATH, 42), ACCENT_LIGHT)
    bottom_statement(d, "ИХ НЕЛЬЗЯ СОГЛАСОВЫВАТЬ ОДИНАКОВО.", y=1100, h=115)
    draw_brand(d, source=True)
    save_slide(im, 2)


def slide3():
    im = make_canvas(3, 220, 175)
    d = ImageDraw.Draw(im)
    draw_border(d); draw_header(d, 3)
    headline(d, ["ТРУДНО ОТМЕНИТЬ?", "ОСТАНОВИТЕСЬ", "И РЕШИТЕ САМИ."], y=120, accent_lines=(0,), max_size=80)
    labels = [
        ((60, 863, 338, 944), "КРУПНЫЙ ПЛАТЁЖ"),
        ((401, 863, 679, 944), "ДОЛГИЙ ДОГОВОР"),
        ((742, 863, 1020, 944), "НАЁМ\nРУКОВОДИТЕЛЯ"),
    ]
    for box, label in labels:
        panel(d, box, radius=14, fill=(8, 10, 11, 225), outline=(129, 90, 58, 230))
        center_text(d, box, label, font(BODY_BOLD_PATH, 23), WHITE)
    bottom_statement(d, "ОШИБКА ЗДЕСЬ МОЖЕТ СТОИТЬ ДОРОГО.", y=1090, h=118)
    draw_brand(d, source=True)
    save_slide(im, 3)


def slide4():
    im = make_canvas(4, 225, 175)
    d = ImageDraw.Draw(im)
    draw_border(d); draw_header(d, 4)
    headline(d, ["ЛЕГКО ИСПРАВИТЬ?", "ПУСТЬ КОМАНДА", "РЕШИТ."], y=120, accent_lines=(2,), max_size=82)
    bottom_statement(d, "НЕ ПОЛУЧИЛОСЬ — ВЕРНУЛИСЬ И ПОПРАВИЛИ.", y=1090, h=118)
    draw_brand(d, source=True)
    save_slide(im, 4)


def slide5():
    im = make_canvas(5, 220, 195)
    d = ImageDraw.Draw(im)
    draw_border(d); draw_header(d, 5)
    headline(d, ["ПЕРЕДАЙТЕ РЕШЕНИЕ.", "ОСТАВЬТЕ 3 ГРАНИЦЫ."], y=120, accent_lines=(1,), max_size=72)
    labels = [
        ((60, 843, 338, 934), "ДО КАКОЙ\nСУММЫ"),
        ((401, 843, 679, 934), "ЧТО НЕЛЬЗЯ\nМЕНЯТЬ"),
        ((742, 843, 1020, 934), "КОГДА\nЗВАТЬ ВАС"),
    ]
    for i, (box, label) in enumerate(labels, 1):
        panel(d, box, radius=14, fill=(8, 10, 11, 232), outline=(164, 92, 50, 235))
        d.ellipse((box[0] + 14, box[1] + 14, box[0] + 45, box[1] + 45), fill=ACCENT)
        number = str(i)
        nf = font(BODY_BOLD_PATH, 18)
        nb = d.textbbox((0, 0), number, font=nf)
        d.text((box[0] + 29.5 - (nb[2] - nb[0]) / 2, box[1] + 29.5 - (nb[3] - nb[1]) / 2 - 2), number, font=nf, fill=WHITE)
        center_text(d, (box[0] + 54, box[1] + 4, box[2] - 10, box[3] - 4), label, font(BODY_BOLD_PATH, 23), WHITE, 4)
    bottom_statement(d, "ВНУТРИ ГРАНИЦ КОМАНДА РЕШАЕТ САМА.", y=1085, h=118)
    draw_brand(d)
    save_slide(im, 5)


def slide6():
    im = make_canvas(6, 230, 190)
    d = ImageDraw.Draw(im)
    draw_border(d); draw_header(d, 6)
    headline(d, ["ВАМ НЕ НУЖНО", "РЕШАТЬ ВСЁ.", "НУЖНО РЕШИТЬ,", "ЧТО МОГУТ РЕШАТЬ", "БЕЗ ВАС."], y=110, accent_lines=(4,), max_size=69, min_size=55)
    bottom_statement(d, "СЕГОДНЯ ОТДАЙТЕ КОМАНДЕ ОДНО РЕШЕНИЕ,\nКОТОРОЕ ЛЕГКО ИСПРАВИТЬ.", y=1080, h=132, accent_second=True)
    draw_brand(d)
    save_slide(im, 6)


def contact_sheet():
    thumbs = []
    for i in range(1, 7):
        im = Image.open(ROOT / f"{i:02d}.jpg").convert("RGB")
        im.thumbnail((324, 405), Image.Resampling.LANCZOS)
        thumbs.append(im.copy())
    gap = 38
    margin = 55
    cw = margin * 2 + 3 * 324 + 2 * gap
    ch = margin * 2 + 2 * 405 + gap
    sheet = Image.new("RGB", (cw, ch), BG)
    for idx, im in enumerate(thumbs):
        x = margin + (idx % 3) * (324 + gap)
        y = margin + (idx // 3) * (405 + gap)
        sheet.paste(im, (x, y))
    sheet.save(ROOT / "contact_sheet.jpg", "JPEG", quality=94, optimize=True)


if __name__ == "__main__":
    slide1(); slide2(); slide3(); slide4(); slide5(); slide6(); contact_sheet()
