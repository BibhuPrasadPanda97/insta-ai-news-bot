"""Free, no-API story selection and writing.

Headlines and summaries in RSS feeds are already written by journalists, so this
reuses them rather than generating text: it scores stories, cleans the headline,
cuts bullets out of the summary and assembles the caption. No key, no cost.
"""
import re

from config import MIN_STORIES, MAX_STORIES, HANDLE

CATEGORIES = [
    ("Chips", r"chip|gpu|semiconductor|silicon|wafer|processor|nvidia|tsmc|foundry|\d+\s?nm"),
    ("Policy", r"regulat|lawsuit|sues?\b|sued|court|antitrust|ban\b|privacy|probe|investigat|"
               r"copyright|ftc\b|\beu\b|senate|congress|ruling|fine[ds]?\b"),
    ("Business", r"rais(e|es|ed|ing)|funding|valuation|acquir|acquisition|merger|ipo\b|"
                 r"revenue|earnings|\$\d|billion|million|invest|layoff|stake|deal\b"),
    ("Models", r"\bmodel\b|gpt|claude|gemini|llama|mistral|\bllm\b|reasoning|benchmark|"
               r"train(ing|ed)?\b|open[- ]source|weights|multimodal|agent"),
]

# Signals that a story is consequential, and what each is worth.
IMPORTANCE = [
    (6, r"launch|unveil|release|announce|introduc|debut|ship"),
    (6, r"rais(e|es|ed)|funding|acquir|acquisition|merger|ipo\b|invest"),
    (5, r"\$\d+(\.\d+)?\s?(b|bn|billion|m|million|trillion)"),
    (5, r"lawsuit|sues?\b|antitrust|regulat|ban\b|ruling|probe"),
    (4, r"breach|hack|outage|vulnerab|leak"),
    (4, r"partnership|partners with|teams up|deal\b"),
    (3, r"\b(gpt|claude|gemini|llama|grok|copilot)\b"),
    (-7, r"best |top \d|deals?\b|review|how to|opinion|why i |guide\b|roundup|vs\.?\b"),
]

BIG_NAMES = (r"OpenAI|Anthropic|Google|DeepMind|Microsoft|Meta|Apple|Amazon|AWS|Nvidia|"
             r"xAI|Grok|Cursor|Perplexity|Tesla|Samsung|TSMC|Intel|AMD|Qualcomm|IBM|"
             r"Oracle|Salesforce|Adobe|GitHub|Hugging Face|Mistral|DeepSeek|Alibaba|"
             r"ByteDance|Baidu|Tencent|Stability|Midjourney|Figma|Notion|Databricks")

# Site names that feeds tack onto the end of a headline.
SITE_SUFFIX = re.compile(r"\s*[|–—-]\s*(TechCrunch|The Verge|Ars Technica|WIRED|"
                         r"VentureBeat|Engadget|MIT Technology Review|Reuters)\s*$", re.I)


JUNK = re.compile(r"best \d|top \d+|deals?\b|\bdeal of\b|review:|hands[- ]on|"
                  r"how to|opinion|why i |guide\b|roundup|explained|vs\.?\b|"
                  r"everything you need to know|what to know|we tried", re.I)


def is_junk(item):
    """Listicles, reviews, deals and opinion pieces are not news."""
    return bool(JUNK.search(item["title"]))


def category(title, summary=""):
    """Classify from the headline first; the summary only decides what it cannot."""
    for text in (title, summary):
        for name, pattern in CATEGORIES:
            if text and re.search(pattern, text, re.I):
                return name
    return "Tools"


def score(item):
    text = f"{item['title']} {item['summary']}"
    total = item.get("outlets", 1) * 4
    for weight, pattern in IMPORTANCE:
        if re.search(pattern, text, re.I):
            total += weight
    if re.search(BIG_NAMES, item["title"]):
        total += 4
    return total


def clean_headline(title, limit=75):
    title = SITE_SUFFIX.sub("", title).strip().strip("—-– ")
    if len(title) <= limit:
        return title
    # Prefer cutting at a clause boundary over chopping mid-thought.
    for sep in (": ", " — ", " - ", ", "):
        head = title.split(sep)[0]
        if 25 <= len(head) <= limit:
            return head
    words, out = title.split(), ""
    for w in words:
        if len(out) + len(w) + 1 > limit - 1:
            break
        out += (" " if out else "") + w
    return out.rstrip(",;: ") + "…"


def sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def bullets(item, limit=105):
    out = []
    for s in sentences(item["summary"]):
        s = s.rstrip(".")
        if len(s) > limit:
            cut = s[:limit]
            if " " not in cut:
                continue
            s = cut.rsplit(" ", 1)[0].rstrip(",;:") + "…"
        if s.lower() not in (b.lower() for b in out):
            out.append(s)
        if len(out) == 3:
            break
    if not out:
        out = [clean_headline(item["title"], limit)]
    return out


def highlight(headline):
    """Words in the headline worth colouring: a figure, else a known company."""
    for pattern in (r"\$\d[\d.,]*\s?(?:billion|million|trillion|B|M|T)?\b",
                    r"\b\d+(?:\.\d+)?x\b", r"\b\d+%", r"\b\d+(?:\.\d+)?\s?nm\b"):
        m = re.search(pattern, headline, re.I)
        if m:
            return [m.group(0)]
    m = re.search(BIG_NAMES, headline)
    if m:
        return [m.group(0)]
    # An acronym or a proper noun reads better as the accent than a verb.
    for w in headline.split():
        bare = w.strip(",.:;'\u2019")
        if len(bare) > 1 and (bare.isupper() or (bare[0].isupper()
                                                 and bare is not headline.split()[0])):
            return [bare]
    words = [w for w in headline.split() if len(w) > 4]
    return [words[0]] if words else [headline.split()[0]]


def company(headline):
    m = re.search(BIG_NAMES, headline)
    return m.group(0) if m else "Tech"


def write(items, day):
    """Same output shape as the Claude writer, so the renderer is unchanged."""
    ranked = sorted(items, key=score, reverse=True)
    stories, per_company = [], {}
    for item in ranked:
        if is_junk(item):
            continue
        headline = clean_headline(item["title"])
        name = company(headline)
        # Don't fill the deck with one firm. "Tech" means unrecognised, so no cap.
        if name != "Tech" and per_company.get(name, 0) >= 2:
            continue
        if any(headline.lower() == s["headline"].lower() for s in stories):
            continue
        per_company[name] = per_company.get(name, 0) + 1
        stories.append({
            "headline": headline,
            "bullets": bullets(item),
            "briefing": " ".join(sentences(item["summary"])[:2])[:320] or headline,
            "source": item["source"],
            "url": item["url"],
            "category": category(item["title"], item["summary"]),
            "highlight": highlight(headline),
            "company": name,
        })
        if len(stories) == MAX_STORIES:
            break
    return {"date": day.strftime("%d %b %Y"), "handle": HANDLE, "stories": stories}
