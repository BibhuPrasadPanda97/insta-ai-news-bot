"""Daily pipeline: fetch -> write -> render -> (optionally) publish."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import fetch_news
import render
import write_stories

OUT = os.environ.get("OUT_DIR", "out")


def main():
    items, day = fetch_news.fetch()
    print(f"{len(items)} deduplicated stories for {day}")
    if len(items) < write_stories.MIN_STORIES:
        raise SystemExit(f"only {len(items)} stories found; not posting")

    data = write_stories.write(items, day)
    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/stories.json", "w") as f:
        json.dump(data, f, indent=2)

    stories, date, handle = data["stories"], data["date"], data["handle"]
    slides = ([render.cover(stories, date, handle)]
              + [render.story_slide(s, i, len(stories), date, handle)
                 for i, s in enumerate(stories, 1)]
              + [render.closing(handle)])
    assert len(slides) <= 10, "Instagram allows at most 10 slides"
    for k, im in enumerate(slides):
        im.convert("RGB").save(f"{OUT}/slide_{k:02d}.jpg", quality=92)

    caption = render.caption(stories, date, handle)
    with open(f"{OUT}/caption.txt", "w") as f:
        f.write(caption)
    print(f"rendered {len(slides)} slides, caption {len(caption)} chars")

    if os.environ.get("PUBLISH") != "1":
        print("PUBLISH is not 1 -- draft only, nothing posted")
        return

    import publish
    urls = json.loads(os.environ["SLIDE_URLS"])   # set by the workflow after upload
    media_id = publish.publish_carousel(urls, caption)
    print(f"published: {media_id}")
    publish.refresh_token()


if __name__ == "__main__":
    main()
