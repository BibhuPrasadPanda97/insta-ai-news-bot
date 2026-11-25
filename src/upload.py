"""Put the rendered slides somewhere Instagram can fetch them.

Instagram's API does not accept file uploads: it fetches each image from a public
HTTPS URL. Two free backends:

  gh_pages  the workflow commits the slides to the `slides` branch and GitHub Pages
            serves them. Needs the repository to be public (or a paid plan), and
            Pages enabled for that branch. No account anywhere else.
  imgbb     posts to api.imgbb.com with a free API key. Works with a private repo.
"""
import base64
import os

import requests


def _gh_pages_urls(paths):
    """The workflow has already pushed the files; just build their URLs."""
    base = os.environ.get("SLIDES_BASE_URL")
    if not base:
        raise RuntimeError("SLIDES_BASE_URL is not set; the gh_pages backend needs it")
    return [f"{base.rstrip('/')}/{os.path.basename(p)}" for p in paths]


def _imgbb_urls(paths):
    key = os.environ.get("IMGBB_API_KEY")
    if not key:
        raise RuntimeError("IMGBB_API_KEY is not set")
    urls = []
    for p in paths:
        with open(p, "rb") as f:
            payload = base64.b64encode(f.read())
        r = requests.post("https://api.imgbb.com/1/upload",
                          data={"key": key, "image": payload}, timeout=120)
        if not r.ok:
            raise RuntimeError(f"imgbb rejected {os.path.basename(p)}: {r.text[:200]}")
        urls.append(r.json()["data"]["url"])
    return urls


BACKENDS = {"gh_pages": _gh_pages_urls, "imgbb": _imgbb_urls}


def slide_urls(paths):
    name = os.environ.get("UPLOADER", "gh_pages")
    try:
        backend = BACKENDS[name]
    except KeyError:
        raise RuntimeError(f"unknown UPLOADER {name!r}; use one of {sorted(BACKENDS)}")
    urls = backend(sorted(paths))
    if not all(u.startswith("https://") for u in urls):
        raise RuntimeError("Instagram needs https URLs")
    return urls
