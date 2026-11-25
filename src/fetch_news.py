"""Fetch RSS items published during the previous IST day, deduplicated."""
import datetime as dt
import re
import sys
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import feedparser

from config import FEEDS, TIMEZONE_OFFSET_HOURS

TRACKING = re.compile(r"^(utm_|fbclid|gclid|ref$|ref_)")
STOPWORDS = {"the", "a", "an", "to", "of", "in", "on", "for", "and", "is", "its",
             "with", "at", "as", "by", "from", "new", "says", "will", "that"}


def ist_now():
    return dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=TIMEZONE_OFFSET_HOURS)


def yesterday_window():
    """UTC start/end of the previous IST calendar day."""
    y = (ist_now() - dt.timedelta(days=1)).date()
    off = dt.timedelta(hours=TIMEZONE_OFFSET_HOURS)
    start = dt.datetime.combine(y, dt.time.min).replace(tzinfo=dt.timezone.utc) - off
    return start, start + dt.timedelta(days=1), y


def clean_url(url):
    p = urlparse(url)
    q = [(k, v) for k, v in parse_qsl(p.query) if not TRACKING.match(k)]
    return urlunparse(p._replace(query=urlencode(q), fragment=""))


def key_words(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def published(entry):
    for field in ("published_parsed", "updated_parsed"):
        t = entry.get(field)
        if t:
            return dt.datetime(*t[:6], tzinfo=dt.timezone.utc)
    return None


def fetch():
    start, end, day = yesterday_window()
    items = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:                      # a dead feed must not kill the run
            print(f"feed failed {url}: {e}", file=sys.stderr)
            continue
        source = feed.feed.get("title", urlparse(url).netloc)
        for e in feed.entries:
            when = published(e)
            if not when or not (start <= when < end):
                continue
            title = (e.get("title") or "").strip()
            link = e.get("link")
            if not title or not link:
                continue
            items.append({
                "title": title,
                "url": clean_url(link),
                "source": urlparse(link).netloc.replace("www.", ""),
                "feed": source,
                "summary": re.sub(r"<[^>]+>", "", e.get("summary", ""))[:600],
                "published": when.isoformat(),
            })
    return dedupe(items), day


def dedupe(items):
    """Group items whose headlines overlap strongly; keep the fullest one."""
    clusters = []
    for it in items:
        words = key_words(it["title"])
        for c in clusters:
            overlap = len(words & c["words"]) / max(1, min(len(words), len(c["words"])))
            if it["url"] == c["items"][0]["url"] or overlap >= 0.6:
                c["items"].append(it)
                c["words"] |= words
                break
        else:
            clusters.append({"words": words, "items": [it]})
    out = []
    for c in clusters:
        best = max(c["items"], key=lambda i: len(i["summary"]))
        best = dict(best, outlets=len({i["source"] for i in c["items"]}))
        out.append(best)
    out.sort(key=lambda i: (-i["outlets"], i["published"]))
    return out


if __name__ == "__main__":
    import json
    items, day = fetch()
    print(json.dumps({"day": day.isoformat(), "items": items}, indent=2))
