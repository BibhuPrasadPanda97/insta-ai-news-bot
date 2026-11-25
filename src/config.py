"""Tunable settings for the daily brief."""
import os

HANDLE = os.environ.get("IG_HANDLE", "@poweraidaily")
TIMEZONE_OFFSET_HOURS = 5.5          # IST
MIN_STORIES, MAX_STORIES = 5, 8      # Instagram allows 10 slides; +cover +closing
MODEL = "claude-opus-5-5"

# General top-tech feeds. Most of what lands here is AI anyway.
FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.wired.com/feed/rss",
    "https://venturebeat.com/feed/",
    "https://www.technologyreview.com/feed/",
    "https://www.engadget.com/rss.xml",
    "https://news.ycombinator.com/rss",
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://blogs.nvidia.com/feed/",
    "https://huggingface.co/blog/feed.xml",
]
