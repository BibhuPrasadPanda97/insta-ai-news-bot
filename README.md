# ai-news-bot

A daily Instagram carousel of the previous day's biggest tech news, posted at 11:00 AM IST.

## How it runs

`.github/workflows/daily.yml` runs `src/run.py` at 05:30 UTC (11:00 IST) and on demand.

1. `fetch_news.py` reads the RSS feeds in `config.py`, keeps items published during the
   previous IST day, strips tracking parameters and clusters duplicate headlines.
2. The writer picks the 5 to 8 biggest stories and produces a headline, three bullets and
   a caption briefing for each. Two backends, chosen with the `WRITER` variable:
   - `rules` (default, **free, no API key**): `write_rules.py` scores stories by how many
     outlets covered them plus keyword signals, drops listicles, reviews, deals and
     opinion pieces, then reuses the journalist-written headline and cuts the bullets out
     of the feed summary.
   - `claude`: `write_stories.py` has Claude read the candidates and write original copy.
     Better headlines and bullets, and it can weigh significance rather than count
     keywords. Needs `ANTHROPIC_API_KEY` and costs a few cents a run.

   To switch, set a repository variable `WRITER` to `claude` (Settings, Secrets and
   variables, Actions, Variables).
3. `render.py` draws the slides (1080x1350 JPEG) and the caption. All text is drawn by the
   script, never by an image model, so it is always spelled correctly.
4. `publish.py` posts the carousel through the Instagram Graph API.

Until `PUBLISH=1` is set, the run only drafts: slides and caption are uploaded as a build
artifact for review and nothing is posted.

## Secrets

Set these in Settings, Secrets and variables, Actions:

| Secret | What it is |
| --- | --- |
| `ANTHROPIC_API_KEY` | Only for `WRITER=claude`. Not needed by default |
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
