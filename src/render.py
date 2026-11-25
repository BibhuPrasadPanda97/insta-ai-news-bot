"""v2: bold, graphic carousel slides. Usage: python render_carousel_v2.py stories.json out_dir
Optional per-story 'bg' = path to an AI-generated image used as a darkened backdrop."""
import json, sys, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1350
_DIRS = ["/usr/share/fonts/opentype/inter/", "/usr/share/fonts/truetype/inter/",
         os.path.join(os.path.dirname(__file__), "fonts") + "/"]
_FALLBACK = {"Inter-Black.otf": "DejaVuSans-Bold.ttf",
             "Inter-ExtraBold.otf": "DejaVuSans-Bold.ttf",
             "Inter-Bold.otf": "DejaVuSans-Bold.ttf",
             "Inter-SemiBold.otf": "DejaVuSans-Bold.ttf",
             "Inter-Medium.otf": "DejaVuSans.ttf",
             "Inter-Regular.otf": "DejaVuSans.ttf"}
_DEJAVU = "/usr/share/fonts/truetype/dejavu/"


def F(n, s):
    """Load a weight of Inter, falling back to DejaVu where Inter is absent."""
    for d in _DIRS:
        if os.path.exists(d + n):
            return ImageFont.truetype(d + n, s)
    alt = _DEJAVU + _FALLBACK.get(n, "DejaVuSans.ttf")
    if os.path.exists(alt):
        return ImageFont.truetype(alt, s)
    return ImageFont.load_default(size=s)

PALETTES = [  # (bg top, bg bottom, accent1, accent2)
    ((20, 10, 60), (5, 5, 25), (255, 70, 150), (120, 80, 255)),
    ((5, 30, 60), (3, 8, 25), (0, 220, 255), (80, 120, 255)),
    ((40, 10, 20), (12, 4, 12), (255, 150, 40), (255, 60, 90)),
    ((5, 40, 40), (3, 12, 18), (60, 255, 170), (0, 180, 255)),
    ((35, 10, 55), (10, 4, 22), (200, 90, 255), (255, 90, 200)),
]

def gradient(top, bot):
    im = Image.new("RGB", (W, H)); px = im.load()
    for y in range(H):
        t = y / (H - 1); c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(W): px[x, y] = c
    return im

def glow(im, cx, cy, r, color, strength=0.55):
    layer = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c * strength) for c in color))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.45))
    return ImageChops.add(im, layer)

def backdrop(pal, seed, bg=None):
    top, bot, a1, a2 = pal; rnd = random.Random(seed)
    if bg and os.path.exists(bg):
        im = Image.open(bg).convert("RGB").resize((W, H))
        im = Image.blend(im, Image.new("RGB", (W, H), bot), 0.55)
    else:
        im = gradient(top, bot)
        im = glow(im, rnd.randint(650, 1000), rnd.randint(80, 350), 420, a1)
        im = glow(im, rnd.randint(0, 300), rnd.randint(900, 1250), 460, a2, 0.45)
    # dot grid + diagonal lines for a techy texture
    d = ImageDraw.Draw(im, "RGBA")
    for gx in range(60, W, 60):
        for gy in range(60, H, 60): d.ellipse([gx-1.5, gy-1.5, gx+1.5, gy+1.5], fill=(255, 255, 255, 28))
    return im

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def pill(d, x, y, text, f, fill, ink=(10, 10, 30), pad=26):
    tw = d.textlength(text, font=f); h = f.size + 24
    d.rounded_rectangle([x, y, x + tw + 2*pad, y + h], h//2, fill=fill)
    d.text((x + pad, y + 10), text, font=f, fill=ink); return x + tw + 2*pad

def shadow_text(im, xy, text, f, fill, blur=10, off=6):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0], xy[1]+off), text, font=f, fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(blur)); im.paste(sh, (0, 0), sh)
    ImageDraw.Draw(im).text(xy, text, font=f, fill=fill)

def story_slide(s, i, n, date, handle, bg=None):
    pal = PALETTES[(i - 1) % len(PALETTES)]; _, _, a1, a2 = pal
    im = backdrop(pal, i, s.get("bg") or bg); d = ImageDraw.Draw(im)
    # giant ghost number
    gf = F("Inter-Black.otf", 700); ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ghost).text((W - 470, -40), str(i), font=gf, fill=a1 + (40,)); im.paste(ghost, (0, 0), ghost)
    d = ImageDraw.Draw(im)
    # top bar: category pill + counter
    pill(d, 70, 70, s["category"].upper(), F("Inter-ExtraBold.otf", 28), a1)
    d.text((W - 70 - d.textlength(f"{i}/{n}", font=F("Inter-Bold.otf", 34)), 82), f"{i}/{n}", font=F("Inter-Bold.otf", 34), fill=(255, 255, 255, 200))
    # headline with highlighted key words
    # Shrink the headline until it fits in four lines rather than clipping it.
    for size in (84, 76, 68, 60, 54):
        hf = F("Inter-Black.otf", size)
        lines = wrap(d, s["headline"].upper(), hf, W - 140)
        if len(lines) <= 4:
            break
    step = int(hf.size * 1.17)
    y = 230
    hl = set(w.lower().strip(".,:!?") for w in s.get("highlight", []))
    for ln in lines:
        x = 70
        for w in ln.split():
            col = a1 if w.lower().strip(".,:!?") in hl else (255, 255, 255)
            shadow_text(im, (x, y), w, hf, col); d = ImageDraw.Draw(im)
            x += d.textlength(w + " ", font=hf)
        y += step
    # accent underline
    d.rounded_rectangle([70, y + 10, 70 + 220, y + 24], 7, fill=a2); y += 70
    # bullet cards (glass), centred in the space left between headline and footer
    bf = F("Inter-SemiBold.otf", 38)
    cards = []
    for b in s["bullets"][:3]:
        lines = wrap(d, b, bf, W - 140 - 110)[:3]
        cards.append((lines, len(lines) * 50 + 44))
    block = sum(h for _, h in cards) + 22 * max(0, len(cards) - 1)
    top, bottom = y, H - 190
    y = max(top, top + (bottom - top - block) // 2)
    for lines, hh in cards:
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([70, y, W - 70, y + hh], 26, fill=(255, 255, 255, 30), outline=(255, 255, 255, 70), width=2)
        im.paste(card, (0, 0), card); d = ImageDraw.Draw(im)
        d.rounded_rectangle([70, y + 16, 82, y + hh - 16], 6, fill=a1)
        ty = y + 22
        for ln in lines: d.text((112, ty), ln, font=bf, fill=(255, 255, 255)); ty += 50
        y += hh + 22
    # footer
    d.text((70, H - 110), "SOURCE  " + s["source"].upper(), font=F("Inter-Bold.otf", 26), fill=(255, 255, 255, 190))
    d.text((70, H - 68), handle, font=F("Inter-Medium.otf", 26), fill=(255, 255, 255, 150))
    sw = F("Inter-ExtraBold.otf", 28); t = "SWIPE  >"
    d.text((W - 70 - d.textlength(t, font=sw), H - 100), t, font=sw, fill=a1)
    return im

def cover(stories, date, handle, bg=None):
    pal = PALETTES[0]; _, _, a1, a2 = pal
    im = backdrop(pal, 99, bg); d = ImageDraw.Draw(im)
    pill(d, 70, 80, "DAILY TECH + AI BRIEF", F("Inter-ExtraBold.otf", 30), a1)
    f1, f2 = F("Inter-Black.otf", 190), F("Inter-Black.otf", 190)
    shadow_text(im, (64, 190), "TOP", f1, (255, 255, 255)); shadow_text(im, (64, 360), "TECH", f1, a1)
    shadow_text(im, (64, 530), "NEWS", f2, (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((70, 770), date.upper(), font=F("Inter-Bold.otf", 44), fill=a2 if sum(a2) > 300 else (255, 255, 255))
    y = 880; tf = F("Inter-SemiBold.otf", 36)
    for k, s in enumerate(stories[:3], 1):
        d.ellipse([70, y, 118, y + 48], fill=a1); d.text((86 if k else 0, y + 6), str(k), font=F("Inter-ExtraBold.otf", 30), fill=(10, 10, 30))
        for ln in wrap(d, s["headline"], tf, W - 260)[:2]: d.text((140, y + 2), ln, font=tf, fill=(255, 255, 255)); y += 46
        y += 30
    d.text((70, H - 100), f"{len(stories)} STORIES  |  SWIPE  >", font=F("Inter-ExtraBold.otf", 32), fill=a1)
    return im

def closing(handle):
    pal = PALETTES[1]; _, _, a1, a2 = pal; im = backdrop(pal, 7); d = ImageDraw.Draw(im)
    shadow_text(im, (70, 430), "FULL", F("Inter-Black.otf", 170), (255, 255, 255))
    shadow_text(im, (70, 600), "BRIEFS", F("Inter-Black.otf", 170), a1)
    d = ImageDraw.Draw(im)
    d.text((70, 820), "in the caption  v", font=F("Inter-Bold.otf", 50), fill=(255, 255, 255))
    pill(d, 70, 960, f"FOLLOW {handle.upper()}", F("Inter-ExtraBold.otf", 34), a1)
    return im

def caption(stories, date, handle):
    out = [f"TOP TECH NEWS | {date}\n"]
    for i, s in enumerate(stories, 1): out.append(f"{i}. {s['headline']}\n{s['briefing']}\nSource: {s['source']}\n")
    out.append(f"Follow {handle} for your daily tech + AI brief.\n\n#TechNews #AI #ArtificialIntelligence #Technology #GenAI #Startups")
    c = "\n".join(out); assert len(c) <= 2200, len(c); return c

if __name__ == "__main__":
    data = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    st, date, handle = data["stories"], data["date"], data.get("handle", "@poweraidaily")
    slides = [cover(st, date, handle, data.get("cover_bg"))] + [story_slide(s, i, len(st), date, handle) for i, s in enumerate(st, 1)] + [closing(handle)]
    assert len(slides) <= 10
    for k, im in enumerate(slides): im.convert("RGB").save(f"{out}/slide_{k:02d}.jpg", quality=92)
    open(f"{out}/caption.txt", "w").write(caption(st, date, handle)); print("rendered", len(slides))
