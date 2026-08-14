from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_source"

W, H = 1080, 1350
SAFE = 72

WHITE = (244, 241, 233)
SOFT = (188, 190, 187)
MUTED = (130, 135, 136)
COPPER = (224, 137, 66)
AMBER = (243, 173, 83)

FONT_HEAD = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def font(path, size):
    return ImageFont.truetype(path, size=size)


def cover(im):
    im = im.convert("RGB")
    scale = max(W / im.width, H / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    return im.crop((left, top, left + W, top + H))


def base_scene(index, top_dark=0.72, bottom_dark=0.10, brightness=0.86):
    im = cover(Image.open(SRC / f"scene{index:02d}.png"))
    im = ImageEnhance.Color(im).enhance(0.78)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Brightness(im).enhance(brightness)
    rgba = im.convert("RGBA")

    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        top_alpha = int(255 * top_dark * max(0, 1 - y / 610))
        bottom_alpha = int(255 * bottom_dark * max(0, (y - 1040) / 310))
        sd.line((0, y, W, y), fill=(2, 4, 5, min(232, top_alpha + bottom_alpha)))
    rgba = Image.alpha_composite(rgba, shade)

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(110):
        alpha = int(88 * (1 - i / 110) ** 2)
        vd.rectangle((i, i, W - i - 1, H - i - 1), outline=alpha)
    black = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black.putalpha(vignette)
    return Image.alpha_composite(rgba, black)


def fit(draw, value, path, max_size, max_width, min_size=18):
    for size in range(max_size, min_size - 1, -1):
        candidate = font(path, size)
        box = draw.textbbox((0, 0), value, font=candidate)
        if box[2] - box[0] <= max_width:
            return candidate
    return font(path, min_size)


def text(draw, xy, value, fnt, fill=WHITE, anchor="la", spacing=5):
    draw.multiline_text(
        xy, value, font=fnt, fill=fill, anchor=anchor, spacing=spacing,
        stroke_width=1, stroke_fill=(0, 0, 0, 145),
    )


def panel(draw, box, radius=22, fill=(7, 10, 12, 226), outline=(118, 79, 48, 175), width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pill(draw, xy, value, width=None, accent=False, size=20):
    fnt = font(FONT_BOLD, size)
    box = draw.textbbox((0, 0), value, font=fnt)
    tw, th = box[2] - box[0], box[3] - box[1]
    pw, ph = width or tw + 30, th + 20
    x, y = xy
    fill = (178, 93, 40, 225) if accent else (14, 18, 20, 228)
    outline = (235, 152, 73, 220) if accent else (111, 115, 114, 145)
    draw.rounded_rectangle((x, y, x + pw, y + ph), radius=ph // 2, fill=fill, outline=outline, width=1)
    draw.text((x + pw / 2, y + ph / 2 - 1), value, font=fnt, fill=WHITE, anchor="mm")
    return pw, ph


def header(draw, index):
    draw.rounded_rectangle((SAFE, 44, SAFE + 13, 57), radius=6, fill=COPPER)
    draw.text((SAFE + 28, 52), "УПРАВЛЕНИЕ • ИИ", font=font(FONT_BOLD, 22), fill=SOFT, anchor="lm")
    draw.text((W - SAFE, 52), f"{index:02d} / 07", font=font(FONT_BOLD, 21), fill=MUTED, anchor="rm")


def footer(draw, source=None):
    y = 1310
    draw.line((SAFE, y - 20, W - SAFE, y - 20), fill=(83, 70, 61, 135), width=1)
    draw.text((SAFE, y), "@hasbulla_gubdenskiy", font=font(FONT_BOLD, 19), fill=SOFT, anchor="lm")
    if source:
        draw.text((W - SAFE, y), source, font=font(FONT_REG, 17), fill=MUTED, anchor="rm")


def save(im, index):
    im.convert("RGB").save(ROOT / f"{index:02d}.jpg", "JPEG", quality=95, subsampling=0, optimize=True)


def slide1():
    im = base_scene(1, top_dark=0.84, bottom_dark=0.06, brightness=0.82)
    d = ImageDraw.Draw(im)
    header(d, 1)
    text(d, (SAFE, 112), "КОМАНДА УЖЕ", font(FONT_HEAD, 74))
    text(d, (SAFE, 184), "ИСПОЛЬЗУЕТ ИИ.", fit(d, "ИСПОЛЬЗУЕТ ИИ.", FONT_HEAD, 82, W - 2 * SAFE))
    text(d, (SAFE, 270), "БИЗНЕС —", font(FONT_HEAD, 82), fill=COPPER)
    text(d, (SAFE, 350), "ЕЩЁ НЕТ.", font(FONT_BLACK, 83), fill=COPPER)
    panel(d, (SAFE, 465, 845, 555), radius=18, fill=(7, 10, 12, 218), outline=(133, 86, 50, 155), width=1)
    text(d, (SAFE + 24, 510), "Как превратить отдельные действия\nв общий порядок работы", font(FONT_BOLD, 27), fill=(229, 226, 218), anchor="lm", spacing=7)
    d.line((SAFE, 582, SAFE + 162, 582), fill=COPPER, width=5)
    footer(d)
    save(im, 1)


def slide2():
    im = base_scene(2, top_dark=0.80, bottom_dark=0.08, brightness=0.86)
    d = ImageDraw.Draw(im)
    header(d, 2)
    text(d, (SAFE, 105), "ИИ УЖЕ ИСПОЛЬЗУЮТ.", fit(d, "ИИ УЖЕ ИСПОЛЬЗУЮТ.", FONT_HEAD, 78, W - 2 * SAFE))
    text(d, (SAFE, 181), "НО БОЛЬШИНСТВО — НОВИЧКИ.", fit(d, "НО БОЛЬШИНСТВО — НОВИЧКИ.", FONT_HEAD, 70, W - 2 * SAFE), fill=COPPER)
    panel(d, (70, 430, 510, 655), radius=24, fill=(7, 10, 12, 230), outline=(114, 117, 117, 165), width=2)
    text(d, (290, 480), "61%", font(FONT_BLACK, 72), fill=WHITE, anchor="ma")
    text(d, (290, 556), "УЧАСТНИКОВ ОПРОСА", font(FONT_REG, 21), fill=SOFT, anchor="ma")
    text(d, (290, 602), "ИСПОЛЬЗУЮТ ИИ", font(FONT_BOLD, 27), fill=WHITE, anchor="ma")
    panel(d, (570, 555, 1010, 805), radius=24, fill=(18, 13, 10, 233), outline=(232, 143, 66, 220), width=2)
    text(d, (790, 608), "76%", font(FONT_BLACK, 72), fill=COPPER, anchor="ma")
    text(d, (790, 680), "ИЗ ТЕХ, КТО ПОЛЬЗУЕТСЯ ИИ, —", fit(d, "ИЗ ТЕХ, КТО ПОЛЬЗУЕТСЯ ИИ, —", FONT_BOLD, 19, 395), fill=SOFT, anchor="ma")
    text(d, (790, 723), "НОВИЧКИ", font(FONT_BLACK, 31), fill=WHITE, anchor="ma")
    text(d, (790, 765), "Простые инструменты. Отдельные задачи.", fit(d, "Простые инструменты. Отдельные задачи.", FONT_REG, 19, 395), fill=SOFT, anchor="ma")
    panel(d, (SAFE, 1067, W - SAFE, 1224), radius=22, fill=(7, 10, 12, 232), outline=(120, 81, 49, 165), width=2)
    text(d, (W / 2, 1110), "ИСПОЛЬЗОВАТЬ ИИ — ЕЩЁ НЕ ЗНАЧИТ", fit(d, "ИСПОЛЬЗОВАТЬ ИИ — ЕЩЁ НЕ ЗНАЧИТ", FONT_BLACK, 28, W - 2 * SAFE - 40), fill=WHITE, anchor="ma")
    text(d, (W / 2, 1153), "ВСТРОИТЬ ЕГО В РАБОТУ", font(FONT_BLACK, 29), fill=COPPER, anchor="ma")
    text(d, (W / 2, 1201), "Опрос не отражает весь малый бизнес", font(FONT_REG, 18), fill=MUTED, anchor="ma")
    footer(d, "Источник: OECD, 2026")
    save(im, 2)


def slide3():
    im = base_scene(3, top_dark=0.80, bottom_dark=0.10, brightness=0.83)
    d = ImageDraw.Draw(im)
    header(d, 3)
    text(d, (SAFE, 105), "ЧАЩЕ ВСЕГО ИИ РЕШАЕТ", fit(d, "ЧАЩЕ ВСЕГО ИИ РЕШАЕТ", FONT_HEAD, 71, W - 2 * SAFE))
    text(d, (SAFE, 177), "ОТДЕЛЬНЫЕ ЗАДАЧИ", fit(d, "ОТДЕЛЬНЫЕ ЗАДАЧИ", FONT_HEAD, 78, W - 2 * SAFE), fill=COPPER)
    panel(d, (65, 560, 505, 810), radius=24, fill=(7, 10, 12, 232), outline=(115, 117, 117, 165), width=2)
    text(d, (285, 615), "56,6%", font(FONT_BLACK, 63), fill=WHITE, anchor="ma")
    text(d, (285, 686), "ОПРОШЕННЫХ", font(FONT_REG, 21), fill=SOFT, anchor="ma")
    text(d, (285, 726), "ИСПОЛЬЗУЮТ ИИ", font(FONT_BOLD, 25), fill=WHITE, anchor="ma")
    text(d, (285, 768), "ДЛЯ ОТДЕЛЬНЫХ ЗАДАЧ", fit(d, "ДЛЯ ОТДЕЛЬНЫХ ЗАДАЧ", FONT_BOLD, 22, 395), fill=SOFT, anchor="ma")
    panel(d, (575, 660, 1015, 930), radius=24, fill=(18, 13, 10, 234), outline=(232, 143, 66, 220), width=2)
    text(d, (795, 714), "19%", font(FONT_BLACK, 63), fill=COPPER, anchor="ma")
    text(d, (795, 774), "ОПРОШЕННЫХ ИСПОЛЬЗУЮТ ИИ", fit(d, "ОПРОШЕННЫХ ИСПОЛЬЗУЮТ ИИ", FONT_BOLD, 21, 395), fill=WHITE, anchor="ma")
    text(d, (795, 817), "В НЕСКОЛЬКИХ НАПРАВЛЕНИЯХ", fit(d, "В НЕСКОЛЬКИХ НАПРАВЛЕНИЯХ", FONT_BOLD, 19, 395), fill=SOFT, anchor="ma")
    text(d, (795, 855), "ИЛИ ВО ВСЁМ БИЗНЕСЕ", fit(d, "ИЛИ ВО ВСЁМ БИЗНЕСЕ", FONT_BOLD, 20, 395), fill=SOFT, anchor="ma")
    panel(d, (SAFE, 1085, W - SAFE, 1224), radius=20, fill=(7, 10, 12, 232), outline=(119, 80, 48, 160), width=2)
    text(d, (W / 2, 1128), "ОТДЕЛЬНЫЕ ЗАДАЧИ ВСТРЕЧАЮТСЯ ЧАЩЕ", fit(d, "ОТДЕЛЬНЫЕ ЗАДАЧИ ВСТРЕЧАЮТСЯ ЧАЩЕ", FONT_BLACK, 27, W - 2 * SAFE - 40), fill=WHITE, anchor="ma")
    text(d, (W / 2, 1173), "1 240 ответов; примерно 3 из 4 — из Японии", fit(d, "1 240 ответов; примерно 3 из 4 — из Японии", FONT_REG, 20, W - 2 * SAFE - 40), fill=MUTED, anchor="ma")
    footer(d, "Источник: OECD, 2026")
    save(im, 3)


def slide4():
    im = base_scene(4, top_dark=0.83, bottom_dark=0.07, brightness=0.88)
    d = ImageDraw.Draw(im)
    header(d, 4)
    text(d, (SAFE, 104), "ИИ ВСТРОЕН В РАБОТУ,", fit(d, "ИИ ВСТРОЕН В РАБОТУ,", FONT_HEAD, 70, W - 2 * SAFE))
    text(d, (SAFE, 175), "ЕСЛИ ЕЁ МОЖНО", font(FONT_HEAD, 75))
    text(d, (SAFE, 249), "ПОВТОРИТЬ", font(FONT_BLACK, 76), fill=COPPER)
    positions = [(50, 693), (243, 628), (432, 575), (659, 632), (850, 690)]
    labels = ["ЗАДАЧА", "ИИ", "ПРОВЕРКА", "СЛЕДУЮЩИЙ ШАГ", "РЕЗУЛЬТАТ"]
    widths = [145, 128, 188, 190, 160]
    for (x, y), label, width in zip(positions, labels, widths):
        pill(d, (x, y), label, width=width, accent=(label == "ИИ"), size=15 if len(label) > 10 else (18 if len(label) > 7 else 20))
    panel(d, (SAFE, 1048, W - SAFE, 1223), radius=24, fill=(7, 10, 12, 234), outline=(131, 85, 49, 180), width=2)
    text(d, (W / 2, 1095), "НЕ ОДИН УДАЧНЫЙ ОТВЕТ.", font(FONT_BLACK, 30), fill=WHITE, anchor="ma")
    text(d, (W / 2, 1144), "А ПОНЯТНЫЙ ПОРЯДОК РАБОТЫ.", fit(d, "А ПОНЯТНЫЙ ПОРЯДОК РАБОТЫ.", FONT_BLACK, 32, W - 2 * SAFE - 50), fill=COPPER, anchor="ma")
    text(d, (W / 2, 1190), "ИИ — только один шаг", font(FONT_REG, 22), fill=SOFT, anchor="ma")
    footer(d, "Источники: OECD • Microsoft, 2026")
    save(im, 4)


def question_card(draw, box, number, lines, accent=False):
    panel(draw, box, radius=20, fill=(10, 13, 15, 234), outline=(231, 143, 68, 215) if accent else (112, 113, 112, 165), width=2)
    x1, y1, x2, y2 = box
    draw.text((x1 + 22, y1 + 24), f"0{number}", font=font(FONT_BLACK, 25), fill=COPPER if accent else MUTED, anchor="la")
    text(draw, (x1 + 22, y1 + 67), lines, font(FONT_BOLD, 23), fill=WHITE, spacing=6)


def slide5():
    im = base_scene(5, top_dark=0.82, bottom_dark=0.08, brightness=0.84)
    d = ImageDraw.Draw(im)
    header(d, 5)
    text(d, (SAFE, 105), "ВОЗЬМИТЕ ОДНУ ЗАДАЧУ.", fit(d, "ВОЗЬМИТЕ ОДНУ ЗАДАЧУ.", FONT_HEAD, 72, W - 2 * SAFE))
    text(d, (SAFE, 183), "ОТВЕТЬТЕ НА 4 ВОПРОСА", fit(d, "ОТВЕТЬТЕ НА 4 ВОПРОСА", FONT_BLACK, 68, W - 2 * SAFE), fill=COPPER)
    question_card(d, (58, 430, 468, 595), 1, "Что здесь\nповторяется?")
    question_card(d, (612, 430, 1022, 595), 2, "Кто проверяет\nрезультат?", accent=True)
    question_card(d, (58, 952, 468, 1117), 3, "Кто меняет\nпорядок работы?")
    question_card(d, (612, 952, 1022, 1117), 4, "Как повторить\nудачный результат?", accent=True)
    panel(d, (230, 690, 850, 862), radius=24, fill=(7, 10, 12, 227), outline=(235, 150, 71, 225), width=2)
    text(d, (540, 731), "ВАЖНО НЕ СКОЛЬКО ЛЮДЕЙ", fit(d, "ВАЖНО НЕ СКОЛЬКО ЛЮДЕЙ", FONT_BLACK, 26, 575), fill=WHITE, anchor="ma")
    text(d, (540, 772), "ПОЛЬЗУЮТСЯ ИИ", font(FONT_BLACK, 28), fill=WHITE, anchor="ma")
    text(d, (540, 817), "ВАЖНО — КАК ОНИ РАБОТАЮТ", fit(d, "ВАЖНО — КАК ОНИ РАБОТАЮТ", FONT_BLACK, 27, 575), fill=COPPER, anchor="ma")
    footer(d, "Источники: OECD • Microsoft, 2026")
    save(im, 5)


def step_card(draw, y, number, title, sub, accent=False):
    x1, x2 = 92, 760
    panel(draw, (x1, y, x2, y + 118), radius=20, fill=(8, 11, 13, 232), outline=(230, 142, 67, 215) if accent else (112, 113, 112, 150), width=2)
    draw.rounded_rectangle((x1 + 18, y + 25, x1 + 83, y + 90), radius=16, fill=(180, 94, 42, 230) if accent else (26, 30, 31, 235), outline=(235, 152, 73, 220) if accent else (102, 106, 106, 145), width=1)
    draw.text((x1 + 50, y + 58), str(number), font=font(FONT_BLACK, 27), fill=WHITE, anchor="mm")
    text(draw, (x1 + 104, y + 35), title, font(FONT_BOLD, 25), fill=WHITE)
    text(draw, (x1 + 104, y + 72), sub, font(FONT_REG, 20), fill=SOFT)


def slide6():
    im = base_scene(6, top_dark=0.83, bottom_dark=0.08, brightness=0.84)
    d = ImageDraw.Draw(im)
    header(d, 6)
    text(d, (SAFE, 104), "НАЧНИТЕ НЕ С ПРОГРАММЫ.", fit(d, "НАЧНИТЕ НЕ С ПРОГРАММЫ.", FONT_HEAD, 72, W - 2 * SAFE))
    text(d, (SAFE, 185), "А С ОДНОЙ ЗАДАЧИ.", fit(d, "А С ОДНОЙ ЗАДАЧИ.", FONT_HEAD, 80, W - 2 * SAFE), fill=COPPER)
    step_card(d, 380, 1, "ЗАДАЧА, КОТОРАЯ ПОВТОРЯЕТСЯ", "Что команда делает снова и снова?")
    step_card(d, 526, 2, "ПОНЯТНЫЙ РЕЗУЛЬТАТ", "Что вы считаете хорошей работой?", accent=True)
    step_card(d, 672, 3, "КТО ПРОВЕРЯЕТ И ОТВЕЧАЕТ", "Кто проверит ответ ИИ и примет решение?")
    step_card(d, 818, 4, "СРАВНИТЕ ДО И ПОСЛЕ", "Что изменилось: время, ошибки или стоимость?", accent=True)
    panel(d, (SAFE, 1048, W - SAFE, 1218), radius=22, fill=(7, 10, 12, 234), outline=(129, 84, 49, 175), width=2)
    text(d, (W / 2, 1100), "ОДНА ПОНЯТНАЯ ЗАДАЧА", font(FONT_BLACK, 31), fill=WHITE, anchor="ma")
    text(d, (W / 2, 1150), "лучше множества случайных попыток", font(FONT_BOLD, 25), fill=COPPER, anchor="ma")
    footer(d)
    save(im, 6)


def slide7():
    im = base_scene(7, top_dark=0.85, bottom_dark=0.07, brightness=0.85)
    d = ImageDraw.Draw(im)
    header(d, 7)
    text(d, (SAFE, 105), "ЗАПРОС К ИИ", font(FONT_HEAD, 80))
    text(d, (SAFE, 181), "ПОМОГАЕТ ОДНОМУ.", fit(d, "ПОМОГАЕТ ОДНОМУ.", FONT_HEAD, 80, W - 2 * SAFE))
    text(d, (SAFE, 265), "ПОНЯТНЫЙ ПРОЦЕСС —", fit(d, "ПОНЯТНЫЙ ПРОЦЕСС —", FONT_HEAD, 76, W - 2 * SAFE), fill=COPPER)
    text(d, (SAFE, 341), "ВСЕЙ КОМАНДЕ.", font(FONT_BLACK, 73), fill=COPPER)
    panel(d, (SAFE, 1017, W - SAFE, 1218), radius=24, fill=(7, 10, 12, 236), outline=(232, 143, 67, 215), width=2)
    text(d, (W / 2, 1062), "ОТПРАВЬТЕ ТОМУ, КТО", font(FONT_BOLD, 25), fill=SOFT, anchor="ma")
    text(d, (W / 2, 1102), "ОТВЕЧАЕТ У ВАС ЗА ИИ", fit(d, "ОТВЕЧАЕТ У ВАС ЗА ИИ", FONT_BLACK, 31, W - 2 * SAFE - 50), fill=WHITE, anchor="ma")
    d.line((290, 1140, 790, 1140), fill=(207, 123, 57, 190), width=2)
    text(d, (W / 2, 1174), "Начните разговор с одного процесса", font(FONT_BOLD, 24), fill=COPPER, anchor="ma")
    footer(d)
    save(im, 7)


def contact_sheet():
    canvas = Image.new("RGB", (2160, 1440), (8, 10, 12))
    d = ImageDraw.Draw(canvas)
    thumb_w, thumb_h = 432, 540
    gap_x, gap_y = 55, 72
    top_x, top_y = 137, 120
    bottom_x = 380
    for idx in range(7):
        slide = Image.open(ROOT / f"{idx + 1:02d}.jpg").convert("RGB")
        slide = slide.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        if idx < 4:
            x, y = top_x + idx * (thumb_w + gap_x), top_y
        else:
            x, y = bottom_x + (idx - 4) * (thumb_w + gap_x), top_y + thumb_h + gap_y
        canvas.paste(slide, (x, y))
        d.rounded_rectangle((x - 3, y - 3, x + thumb_w + 3, y + thumb_h + 3), radius=6, outline=(111, 74, 46), width=2)
    canvas.save(ROOT / "contact_sheet.jpg", "JPEG", quality=94, subsampling=0, optimize=True)


if __name__ == "__main__":
    slide1()
    slide2()
    slide3()
    slide4()
    slide5()
    slide6()
    slide7()
    contact_sheet()
    for path in sorted(ROOT.glob("0*.jpg")):
        with Image.open(path) as im:
            assert im.size == (W, H), (path.name, im.size)
    print("Rendered 7 slides and contact sheet at 1080x1350.")
