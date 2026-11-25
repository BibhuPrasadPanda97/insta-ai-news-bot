"""Ask Claude to pick the day's biggest stories and write slides + caption."""
import json
import os

import anthropic

from config import MODEL, MIN_STORIES, MAX_STORIES, HANDLE

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["stories"],
    "properties": {
        "stories": {
            "type": "array",
            "minItems": MIN_STORIES,
            "maxItems": MAX_STORIES,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["headline", "bullets", "briefing", "source", "url",
                             "category", "highlight"],
                "properties": {
                    "headline": {"type": "string", "maxLength": 75},
                    "bullets": {
                        "type": "array", "minItems": 3, "maxItems": 3,
                        "items": {"type": "string", "maxLength": 105},
                    },
                    "briefing": {"type": "string", "maxLength": 320},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                    "category": {"type": "string",
                                 "enum": ["Models", "Business", "Chips", "Policy", "Tools"]},
                    "highlight": {
                        "type": "array", "minItems": 1, "maxItems": 3,
                        "items": {"type": "string"},
                        "description": "Words from the headline to colour as the accent.",
                    },
                },
            },
        }
    },
}

PROMPT = """You are the editor of a daily tech-news Instagram carousel.

Below are candidate stories published yesterday ({day}), already deduplicated.
`outlets` is how many outlets covered the story, a signal of how big it is.

Pick the {lo} to {hi} most significant and write the carousel.

Rules:
- Favour major product and model launches, big funding and acquisitions, chip and
  infrastructure news, regulation and lawsuits, and significant security incidents.
- Skip opinion pieces, listicles, deals and reviews.
- At most two stories about the same company.
- headline: punchy, under 75 characters, states what happened. No clickbait.
- highlight: one to three words taken verbatim from your headline, the ones worth
  colouring. They must appear in the headline exactly as written.
- bullets: three facts, each under 105 characters, from the source material only.
- briefing: two or three sentences for the caption, more detail than the bullets.
- source: the plain domain, for example techcrunch.com. url: the article link.
- Invent nothing. If something is a report or a rumour, say so.

Candidates:
{candidates}
"""


def write(items, day):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    slim = [{k: i[k] for k in ("title", "source", "url", "summary", "outlets")}
            for i in items[:80]]
    msg = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "high",
                       "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": PROMPT.format(
            day=day, lo=MIN_STORIES, hi=MAX_STORIES,
            candidates=json.dumps(slim, indent=1))}],
    )
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"model declined: {msg.stop_details}")
    text = "".join(b.text for b in msg.content if b.type == "text")
    data = json.loads(text)
    return {"date": day.strftime("%d %b %Y"), "handle": HANDLE,
            "stories": data["stories"]}
