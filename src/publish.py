"""Publish a carousel to Instagram through the Graph API."""
import os
import time

import requests

GRAPH = "https://graph.instagram.com/v23.0"


def _post(path, **params):
    r = requests.post(f"{GRAPH}/{path}", data=params, timeout=60)
    if not r.ok:
        raise RuntimeError(f"{path} failed: {r.status_code} {r.text}")
    return r.json()


def _wait(container_id, token, timeout=300):
    """Block until a media container is FINISHED."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"{GRAPH}/{container_id}",
                         params={"fields": "status_code,status",
                                 "access_token": token}, timeout=30).json()
        status = r.get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"container {container_id} errored: {r}")
        time.sleep(5)
    raise TimeoutError(f"container {container_id} never finished")


def publish_carousel(image_urls, caption):
    """image_urls must be public https JPEG links. Returns the new media id."""
    token = os.environ["IG_ACCESS_TOKEN"]
    user = os.environ["IG_USER_ID"]
    if not 2 <= len(image_urls) <= 10:
        raise ValueError("a carousel needs 2 to 10 images")

    children = []
    for url in image_urls:
        c = _post(f"{user}/media", image_url=url, is_carousel_item="true",
                  access_token=token)
        _wait(c["id"], token)
        children.append(c["id"])

    parent = _post(f"{user}/media", media_type="CAROUSEL",
                   children=",".join(children), caption=caption,
                   access_token=token)
    _wait(parent["id"], token)
    return _post(f"{user}/media_publish", creation_id=parent["id"],
                 access_token=token)["id"]


def refresh_token():
    """Extend the long-lived token; run on every scheduled run."""
    token = os.environ["IG_ACCESS_TOKEN"]
    r = requests.get(f"{GRAPH}/refresh_access_token",
                     params={"grant_type": "ig_refresh_token",
                             "access_token": token}, timeout=30)
    return r.json() if r.ok else None
