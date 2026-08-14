from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_source"

W, H = 1080, 1350
SAFE = 74

BG = (10, 12, 14)
WHITE = (242, 239, 231)
SOFT = (176, 183, 187)
MUTED = (125, 133, 139)
COPPER = (213, 126, 61)
AMBER = (235, 160, 76)
LINE = (101, 68, 46)

FONT_HEAD = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def f(path, size):
    return ImageFont.truetype(path, size=size)


def cover(im):
    im = im.convert("RGB")
    scale = max(W / im.width, H / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    return im.crop((left, top, left + W, top + H))


def base_scene(index, top_dark=0.68, bottom_dark=0.16):
    im = cover(Image.open(SRC / f"scene{index:02d}.png"))
    im = ImageEnhance.Color(im).enhance(0.72)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Brightness(im).enhance(0.88)
    rgba = im.convert("RGBA")

    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        top_alpha = int(255 * top_dark * max(0, 1 - y / 630))
        bottom_alpha = int(255 * bottom_dark * max(0, (y - 1060) / 290))
        side = int(42 * abs((y / H) - 0.5))
        alpha = min(230, top_alpha + bottom_alpha + side)
        sd.line((0, y, W, y), fill=(3, 5, 6, alpha))
    rgba = Image.alpha_composite(rgba, shade)

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(120):
        a = int(105 * (1 - i / 120) ** 2)
        vd.rectangle((i, i, W - i - 1, H - i - 1), outline=a)
    black = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black.putalpha(vignette)
    return Image.alpha_composite(rgba, black)


def txt(draw, xy, value, font, fill=WHITE, anchor="la", spacing=4, stroke=0):
    draw.multiline_text(
        xy, value, font=font, fill=fill, anchor=anchor,
        spacing=spacing, stroke_width=stroke, stroke_fill=(0, 0, 0, 170)
    )


def fit_font(draw, value, path, max_size, max_width, min_size=20):
    size = max_size
    while size > min_size:
        font = f(path, size)
        box = draw.textbbox((0, 0), value, font=font)
        if box[2] - box[0] <= max_width:
            return font
        size -= 1
    return f(path, min_size)


def panel(draw, box, radius=22, fill=(8, 11, 13, 218), outline=(119, 78, 48, 185), width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pill(draw, xy, value, width=None, accent=False, font_size=23):
    font = f(FONT_BOLD, font_size)
    box = draw.textbbox((0, 0), value, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    pw = width or tw + 30
    ph = th + 22
    x, y = xy
    fill = (173, 92, 42, 222) if accent else (17, 21, 24, 224)
    outline = (229, 150, 77, 210) if accent else (105, 112, 117, 145)
    draw.rounded_rectangle((x, y, x + pw, y + ph), radius=ph // 2, fill=fill, outline=outline, width=1)
    draw.text((x + pw / 2, y + ph / 2 - 1), value, font=font, fill=WHITE, anchor="mm")
    return pw, ph


def header(draw, index, category="ФИНАНСЫ • НАЛОГИ"):
    draw.rounded_rectangle((SAFE, 44, SAFE + 13, 57), radius=6, fill=COPPER)
    draw.text((SAFE + 28, 52), category, font=f(FONT_BOLD, 22), fill=SOFT, anchor="lm")
    draw.text((W - SAFE, 52), f"{index:02d} / 08", font=f(FONT_BOLD, 21), fill=MUTED, anchor="rm")


def footer(draw, source=None):
    y = 1310
    draw.line((SAFE, y - 20, W - SAFE, y - 20), fill=(83, 72, 64, 130), width=1)
    draw.text((SAFE, y), "@hasbulla_gubdenskiy", font=f(FONT_BOLD, 19), fill=SOFT, anchor="lm")
    if source:
        draw.text((W - SAFE, y), source, font=f(FONT_REG, 18), fill=MUTED, anchor="rm")


def save(im, index):
    out = ROOT / f"{index:02d}.jpg"
    im.convert("RGB").save(out, "JPEG", quality=95, subsampling=0, optimize=True)


def contact_sheet():
    canvas = Image.new("RGB", (2160, 1440), (8, 10, 12))
    draw = ImageDraw.Draw(canvas)
    thumb_w, thumb_h = 480, 600
    gap_x, gap_y = 40, 42
    start_x, start_y = 60, 99
    for idx in range(8):
        slide = Image.open(ROOT / f"{idx + 1:02d}.jpg").convert("RGB")
        slide = slide.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        col, row = idx % 4, idx // 4
        x = start_x + col * (thumb_w + gap_x)
        y = start_y + row * (thumb_h + gap_y)
        canvas.paste(slide, (x, y))
        draw.rounded_rectangle((x - 3, y - 3, x + thumb_w + 3, y + thumb_h + 3), radius=5, outline=(97, 67, 45), width=2)
    canvas.save(ROOT / "contact_sheet.jpg", "JPEG", quality=94, subsampling=0, optimize=True)


def slide1():
    im = base_scene(1, top_dark=0.78, bottom_dark=0.11)
    d = ImageDraw.Draw(im)
    header(d, 1)
    txt(d, (SAFE, 115), "20 МЛН РУБ.", fit_font(d, "20 МЛН РУБ.", FONT_BLACK, 112, W - 2 * SAFE), fill=COPPER, spacing=0)
    txt(d, (SAFE, 258), "И БИЗНЕС УЖЕ", fit_font(d, "И БИЗНЕС УЖЕ", FONT_HEAD, 83, W - 2 * SAFE), fill=WHITE)
    txt(d, (SAFE, 342), "С НДС", f(FONT_HEAD, 98), fill=WHITE)
    panel(d, (SAFE, 450, 820, 536), radius=18, fill=(10, 13, 15, 220), outline=(124, 83, 52, 145), width=1)
    txt(d, (SAFE + 24, 493), "Что собственнику на УСН нужно\nпересчитать в 2026 году", f(FONT_BOLD, 27), fill=(224, 221, 214), anchor="lm", spacing=6)
    d.line((SAFE, 562, SAFE + 150, 562), fill=COPPER, width=5)
    footer(d, "ФНС • 2026")
    save(im, 1)


def slide2():
    im = base_scene(2, top_dark=0.72, bottom_dark=0.08)
    d = ImageDraw.Draw(im)
    header(d, 2)
    txt(d, (SAFE, 105), "ПОРОГ СНИЗИЛСЯ", f(FONT_HEAD, 71), fill=WHITE)
    txt(d, (SAFE, 177), "ВТРОЕ", f(FONT_BLACK, 96), fill=COPPER)
    labels = [
        (66, 462, "2025", "60 МЛН РУБ.", False),
        (285, 664, "2026", "20 МЛН РУБ.", True),
        (540, 815, "2027", "15 МЛН РУБ.", False),
        (800, 952, "2028", "10 МЛН РУБ.", False),
    ]
    for x, y, year, amount, active in labels:
        box_w = 222
        panel(d, (x, y, x + box_w, y + 112), radius=18,
              fill=(22, 18, 15, 228) if active else (9, 12, 14, 220),
              outline=(224, 137, 67, 220) if active else (102, 104, 104, 135), width=2)
        txt(d, (x + 16, y + 27), year, f(FONT_BOLD, 21), fill=COPPER if active else SOFT)
        txt(d, (x + 16, y + 65), amount, fit_font(d, amount, FONT_BOLD, 31, box_w - 32), fill=WHITE)
    panel(d, (SAFE, 1124, W - SAFE, 1232), radius=20, fill=(8, 11, 13, 226), outline=(115, 78, 50, 145), width=1)
    txt(d, (W / 2, 1175), "Порог освобождения от НДС при УСН\nснижается поэтапно", f(FONT_BOLD, 27), fill=(225, 222, 215), anchor="mm", spacing=7)
    footer(d, "Источник: ФНС России")
    save(im, 2)


def slide3():
    im = base_scene(3, top_dark=0.76, bottom_dark=0.09)
    d = ImageDraw.Draw(im)
    header(d, 3)
    txt(d, (SAFE, 105), "ПРОВЕРЯЮТ", f(FONT_HEAD, 73), fill=WHITE)
    txt(d, (SAFE, 176), "ДВА ПЕРИОДА", f(FONT_HEAD, 79), fill=COPPER)
    txt(d, (SAFE, 272), "Обязанность может запустить любой из двух счётчиков", f(FONT_BOLD, 28), fill=SOFT)
    panel(d, (SAFE, 414, 680, 638), radius=22, fill=(8, 11, 13, 226), outline=(104, 108, 110, 150), width=2)
    pill(d, (SAFE + 22, 435), "ДОХОД ЗА 2025")
    txt(d, (SAFE + 22, 504), "> 20 МЛН РУБ.", fit_font(d, "> 20 МЛН РУБ.", FONT_BLACK, 46, 555), fill=WHITE)
    txt(d, (SAFE + 22, 574), "НДС с 01.01.2026", f(FONT_BOLD, 29), fill=COPPER)
    panel(d, (SAFE, 759, 795, 1008), radius=22, fill=(8, 11, 13, 228), outline=(203, 120, 58, 180), width=2)
    pill(d, (SAFE + 22, 781), "ДОХОД С НАЧАЛА 2026", accent=True)
    txt(d, (SAFE + 22, 850), "> 20 МЛН РУБ.", fit_font(d, "> 20 МЛН РУБ.", FONT_BLACK, 46, 665), fill=WHITE)
    txt(d, (SAFE + 22, 918), "НДС с 1-го числа", f(FONT_BOLD, 29), fill=COPPER)
    txt(d, (SAFE + 22, 957), "следующего месяца", f(FONT_BOLD, 27), fill=WHITE)
    panel(d, (SAFE, 1084, W - SAFE, 1228), radius=20, fill=(8, 11, 13, 226), outline=(112, 78, 51, 145), width=1)
    txt(d, (W / 2, 1155), "Проверять нужно и прошлый год,\nи накопленный доход текущего", f(FONT_BOLD, 27), fill=(228, 225, 218), anchor="mm", spacing=7)
    footer(d, "Источник: ФНС России")
    save(im, 3)


def slide4():
    im = base_scene(4, top_dark=0.73, bottom_dark=0.10)
    # Blur generated pseudo-writing on the expense receipts before layout.
    crop = im.crop((780, 790, 1080, 1115)).filter(ImageFilter.GaussianBlur(3.5))
    im.paste(crop, (780, 790))
    d = ImageDraw.Draw(im)
    header(d, 4)
    txt(d, (SAFE, 105), "ПОРОГ — НЕ ОСТАТОК", f(FONT_HEAD, 68), fill=WHITE)
    txt(d, (SAFE, 173), "НА СЧЁТЕ", f(FONT_HEAD, 81), fill=COPPER)
    pill(d, (88, 485), "РЕАЛИЗАЦИЯ", width=255)
    pill(d, (716, 485), "ВНЕРЕАЛИЗАЦИОННЫЕ", width=300, font_size=18)
    panel(d, (338, 712, 742, 832), radius=18, fill=(8, 11, 13, 222), outline=(224, 135, 65, 210), width=2)
    txt(d, (540, 752), "ПОРОГ", f(FONT_BOLD, 22), fill=SOFT, anchor="ma")
    txt(d, (540, 781), "20 МЛН РУБ.", fit_font(d, "20 МЛН РУБ.", FONT_BLACK, 43, 365), fill=WHITE, anchor="ma")
    panel(d, (SAFE, 1024, W - SAFE, 1198), radius=22, fill=(9, 12, 14, 230), outline=(118, 81, 52, 160), width=2)
    txt(d, (SAFE + 28, 1068), "Считаются доходы по правилам УСН:", f(FONT_BOLD, 27), fill=SOFT)
    txt(d, (SAFE + 28, 1114), "реализация + внереализационные доходы", fit_font(d, "реализация + внереализационные доходы", FONT_BOLD, 31, W - 2 * SAFE - 56), fill=WHITE)
    txt(d, (SAFE + 28, 1162), "Расходы порог не уменьшают", f(FONT_BOLD, 28), fill=COPPER)
    footer(d, "Источник: ФНС России")
    save(im, 4)


def slide5():
    im = base_scene(5, top_dark=0.78, bottom_dark=0.12)
    d = ImageDraw.Draw(im)
    header(d, 5)
    txt(d, (SAFE, 104), "МЕНЬШАЯ СТАВКА", f(FONT_HEAD, 70), fill=WHITE)
    txt(d, (SAFE, 174), "НЕ ВСЕГДА ВЫГОДНЕЕ", fit_font(d, "НЕ ВСЕГДА ВЫГОДНЕЕ", FONT_HEAD, 75, W - 2 * SAFE), fill=COPPER)
    panel(d, (72, 620, 512, 790), radius=22, fill=(7, 10, 12, 225), outline=(112, 117, 120, 150), width=2)
    txt(d, (292, 663), "22 / 10 / 0%", f(FONT_BLACK, 44), fill=WHITE, anchor="ma")
    txt(d, (292, 728), "С ВЫЧЕТАМИ", f(FONT_BOLD, 25), fill=SOFT, anchor="ma")
    panel(d, (568, 620, 1008, 790), radius=22, fill=(16, 12, 10, 228), outline=(224, 137, 68, 210), width=2)
    txt(d, (788, 663), "5 / 7%", f(FONT_BLACK, 51), fill=COPPER, anchor="ma")
    txt(d, (788, 727), "БЕЗ ВЫЧЕТА ВХОДНОГО НДС", fit_font(d, "БЕЗ ВЫЧЕТА ВХОДНОГО НДС", FONT_BOLD, 24, 396), fill=WHITE, anchor="ma")
    panel(d, (SAFE, 1052, W - SAFE, 1224), radius=22, fill=(8, 11, 13, 232), outline=(124, 83, 51, 175), width=2)
    txt(d, (W / 2, 1102), "Считать нужно итог,", f(FONT_BLACK, 35), fill=WHITE, anchor="ma")
    txt(d, (W / 2, 1150), "а не выбирать меньшую цифру", f(FONT_BOLD, 30), fill=COPPER, anchor="ma")
    txt(d, (W / 2, 1192), "ФНС: сравнивать структуру затрат и покупателей", f(FONT_REG, 22), fill=SOFT, anchor="ma")
    footer(d, "Источник: ФНС России")
    save(im, 5)


def slide6():
    im = base_scene(6, top_dark=0.74, bottom_dark=0.08)
    d = ImageDraw.Draw(im)
    header(d, 6)
    txt(d, (SAFE, 104), "НДС НУЖНО КУДА-ТО", fit_font(d, "НДС НУЖНО КУДА-ТО", FONT_HEAD, 72, W - 2 * SAFE), fill=WHITE)
    txt(d, (SAFE, 174), "ПОМЕСТИТЬ", f(FONT_HEAD, 88), fill=COPPER)
    pill(d, (428, 700), "НДС", width=222, accent=True, font_size=28)
    panel(d, (74, 616, 456, 794), radius=22, fill=(8, 11, 13, 232), outline=(117, 119, 120, 170), width=2)
    txt(d, (265, 650), "В ЦЕНУ", f(FONT_BLACK, 31), fill=WHITE, anchor="ma")
    txt(d, (265, 700), "меняется цена", f(FONT_BOLD, 25), fill=SOFT, anchor="ma")
    txt(d, (265, 737), "для покупателя", f(FONT_BOLD, 25), fill=SOFT, anchor="ma")
    panel(d, (624, 616, 1006, 794), radius=22, fill=(17, 13, 10, 234), outline=(225, 137, 67, 215), width=2)
    txt(d, (815, 650), "В МАРЖУ", f(FONT_BLACK, 31), fill=COPPER, anchor="ma")
    txt(d, (815, 700), "меньше остаётся", f(FONT_BOLD, 25), fill=WHITE, anchor="ma")
    txt(d, (815, 737), "бизнесу", f(FONT_BOLD, 25), fill=WHITE, anchor="ma")
    panel(d, (SAFE, 1035, W - SAFE, 1217), radius=22, fill=(8, 11, 13, 232), outline=(126, 84, 52, 180), width=2)
    txt(d, (W / 2, 1081), "ПОД ВЫБРАННЫЙ СЦЕНАРИЙ", f(FONT_BOLD, 24), fill=COPPER, anchor="ma")
    txt(d, (W / 2, 1125), "пересчитать договоры", f(FONT_BLACK, 31), fill=WHITE, anchor="ma")
    txt(d, (W / 2, 1167), "и денежный поток", f(FONT_BLACK, 31), fill=WHITE, anchor="ma")
    footer(d)
    save(im, 6)


def slide7():
    im = base_scene(7, top_dark=0.78, bottom_dark=0.11)
    d = ImageDraw.Draw(im)
    header(d, 7)
    txt(d, (SAFE, 105), "ПЕРЕД ВЫБОРОМ —", f(FONT_HEAD, 72), fill=WHITE)
    txt(d, (SAFE, 176), "4 РАСЧЁТА", f(FONT_BLACK, 93), fill=COPPER)
    items = [
        (62, 505, "1", "Цена выдержит НДС?"),
        (574, 505, "2", "Сколько входного НДС\nв закупках?"),
        (62, 924, "3", "Кто покупатели:\nB2B или B2C?"),
        (574, 924, "4", "Что останется\nв марже и деньгах?"),
    ]
    for x, y, num, label in items:
        panel(d, (x, y, x + 444, y + 132), radius=20, fill=(8, 11, 13, 228), outline=(115, 81, 54, 160), width=2)
        d.ellipse((x + 18, y + 33, x + 78, y + 93), fill=(181, 98, 44, 230), outline=(235, 158, 80, 220), width=1)
        txt(d, (x + 48, y + 62), num, f(FONT_BLACK, 25), fill=WHITE, anchor="mm")
        txt(d, (x + 96, y + 66), label, fit_font(d, max(label.split("\n"), key=len), FONT_BOLD, 27, 320), fill=WHITE, anchor="lm", spacing=4)
    panel(d, (SAFE, 1148, W - SAFE, 1232), radius=20, fill=(17, 13, 10, 230), outline=(221, 134, 65, 200), width=2)
    txt(d, (W / 2, 1190), "Считать вместе с бухгалтером / налоговым специалистом", fit_font(d, "Считать вместе с бухгалтером / налоговым специалистом", FONT_BOLD, 27, W - 2 * SAFE - 42), fill=WHITE, anchor="mm")
    footer(d)
    save(im, 7)


def slide8():
    im = base_scene(8, top_dark=0.80, bottom_dark=0.15)
    d = ImageDraw.Draw(im)
    header(d, 8)
    txt(d, (SAFE, 104), "РОСТ НУЖНО СЧИТАТЬ", fit_font(d, "РОСТ НУЖНО СЧИТАТЬ", FONT_HEAD, 74, W - 2 * SAFE), fill=WHITE)
    txt(d, (SAFE, 177), "ДО ПОРОГА — И ПОСЛЕ", fit_font(d, "ДО ПОРОГА — И ПОСЛЕ", FONT_HEAD, 78, W - 2 * SAFE), fill=COPPER)
    pill(d, (86, 671), "ДО ПОРОГА", width=260, font_size=22)
    pill(d, (735, 671), "ПОСЛЕ ПОРОГА", width=260, accent=True, font_size=21)
    panel(d, (SAFE, 1024, W - SAFE, 1192), radius=22, fill=(8, 11, 13, 232), outline=(126, 84, 52, 180), width=2)
    txt(d, (W / 2, 1078), "НДС — изменение модели бизнеса,", f(FONT_BLACK, 31), fill=WHITE, anchor="ma")
    txt(d, (W / 2, 1122), "а не дата в календаре бухгалтера", f(FONT_BOLD, 29), fill=COPPER, anchor="ma")
    panel(d, (SAFE + 102, 1205, W - SAFE - 102, 1264), radius=29, fill=(181, 96, 43, 230), outline=(237, 158, 78, 220), width=1)
    txt(d, (W / 2, 1234), "СОХРАНИТЕ И РАЗБЕРИТЕ СЦЕНАРИИ НА СВОИХ ЦИФРАХ", fit_font(d, "СОХРАНИТЕ И РАЗБЕРИТЕ СЦЕНАРИИ НА СВОИХ ЦИФРАХ", FONT_BOLD, 23, W - 2 * SAFE - 250), fill=WHITE, anchor="mm")
    footer(d)
    save(im, 8)


def main():
    slide1()
    slide2()
    slide3()
    slide4()
    slide5()
    slide6()
    slide7()
    slide8()
    contact_sheet()


if __name__ == "__main__":
    main()
