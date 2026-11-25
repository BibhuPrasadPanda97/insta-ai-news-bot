# ai-news-bot

A daily Instagram carousel of the previous day's biggest tech news, posted at 11:00 AM IST.

## How it runs

`.github/workflows/daily.yml` runs `src/run.py` at 05:30 UTC (11:00 IST) and on demand.

1. `fetch_news.py` reads the RSS feeds in `config.py`, keeps items published during the
   previous IST day, strips tracking parameters and clusters duplicate headlines.
2. `write_stories.py` asks Claude to pick the 5 to 8 biggest stories and write a headline,
   three bullets and a caption briefing for each, as validated JSON.
3. `render.py` draws the slides (1080x1350 JPEG) and the caption. All text is drawn by the
   script, never by an image model, so it is always spelled correctly.
4. `publish.py` posts the carousel through the Instagram Graph API.

Until `PUBLISH=1` is set, the run only drafts: slides and caption are uploaded as a build
artifact for review and nothing is posted.

## Secrets

Set these in Settings, Secrets and variables, Actions:

| Secret | What it is |
| --- | --- |
| `ANTHROPIC_API_KEY` | Anthropic API key, for ranking and writing |
| `IG_ACCESS_TOKEN` | Long-lived Instagram access token (60 days, refreshed on each run) |
| `IG_USER_ID` | Instagram professional account ID |
| `META_APP_ID` | Meta app ID |
| `META_APP_SECRET` | Meta app secret |

## Still to wire

Instagram fetches carousel images from a public URL, so the slides need to be uploaded
somewhere public before `publish_carousel` is called, and the URLs passed in `SLIDE_URLS`.

## Local run

```
pip install -r requirements.txt
ANTHROPIC_API_KEY=... python src/run.py     # drafts into out/
```
