#!/usr/bin/env python3
"""Weekly Reddit pain-point scan for Kyarinko's audience research.

Uses Reddit's official API (app-only OAuth, read-only), ~1 request/second.
Credentials live OUTSIDE the repo in ~/.config/kyarinko/reddit.json:
  {"client_id": "...", "client_secret": "...", "username": "your_reddit_name"}
(make a "script" app at https://www.reddit.com/prefs/apps). Saves no usernames.
Usage: python3 scripts/reddit_scan.py [--config config.json] [--out scans]
"""
import argparse, base64, datetime as dt, json, os, sys, time, urllib.parse, urllib.request

CREDS = os.path.expanduser("~/.config/kyarinko/reddit.json")
API = "https://oauth.reddit.com"

def load_creds():
    try:
        c = json.load(open(CREDS))
        return c["client_id"], c["client_secret"], c.get("username", "unknown")
    except (OSError, ValueError, KeyError):
        sys.exit(f"Missing or broken {CREDS} (needs client_id, client_secret, username). See docstring.")

def get_token(cid, secret, ua):
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=b"grant_type=client_credentials",
        headers={"User-Agent": ua,
                 "Authorization": "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode()})
    with urllib.request.urlopen(req, timeout=30) as r:
        tok = json.load(r).get("access_token")
    if not tok:
        sys.exit("Reddit gave no token: check client_id/client_secret.")
    return tok

def fetch(url, token, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Authorization": f"bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def posts_from(listing):
    for child in listing.get("data", {}).get("children", []):
        d = child.get("data", {})
        if d.get("stickied") or d.get("over_18"):
            continue
        yield {
            "id": d.get("id"),
            "subreddit": d.get("subreddit"),
            "title": (d.get("title") or "").strip(),
            "excerpt": " ".join((d.get("selftext") or "").split())[:500],
            "score": d.get("score", 0),
            "comments": d.get("num_comments", 0),
            "url": "https://www.reddit.com" + (d.get("permalink") or ""),
            "created": dt.datetime.fromtimestamp(d.get("created_utc", 0), dt.timezone.utc).date().isoformat(),
        }

def rank(p):
    return p["score"] + 2 * p["comments"]

def digest_md(posts, date, cfg):
    lines = [f"# Reddit scan {date}", "",
             f"Subreddits: {', '.join(cfg['subreddits'])}. Window: past {cfg['days']}. Top {len(posts)} by upvotes + 2×comments. No usernames.",
             "Use to understand problems; never quote posts or show usernames in videos.", ""]
    for i, p in enumerate(posts, 1):
        lines.append(f"{i}. **{p['title']}** (r/{p['subreddit']}, ↑{p['score']}, 💬{p['comments']}, {p['created']})")
        if p["excerpt"]:
            lines.append(f"   > {p['excerpt'][:280]}")
        lines.append(f"   {p['url']}")
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--out", default="scans")
    ap.add_argument("--from-file", help="parse a saved listing JSON instead of fetching (tests)")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    seen = {}
    if a.from_file:
        for p in posts_from(json.load(open(a.from_file))):
            seen[p["id"]] = p
    else:
        cid, secret, user = load_creds()
        ua = f"macos:kyarinko-research:0.2 (by /u/{user})"
        token = get_token(cid, secret, ua)
        errors = 0
        for sub in cfg["subreddits"]:
            for q in cfg["queries"]:
                url = (f"{API}/r/{sub}/search?"
                       + urllib.parse.urlencode({"q": q, "restrict_sr": 1, "sort": "top", "t": cfg["days"], "limit": cfg["per_query"], "raw_json": 1}))
                try:
                    for p in posts_from(fetch(url, token, ua)):
                        seen[p["id"]] = p
                except Exception as e:
                    errors += 1
                    print(f"skip r/{sub} '{q}': {e}", file=sys.stderr)
                    if errors >= 5 and not seen:
                        sys.exit("Reddit is refusing requests (blocked or rate-limited). Stopping.")
                time.sleep(1.2)
    top = sorted(seen.values(), key=rank, reverse=True)[: cfg["top_n"]]
    date = dt.date.today().isoformat()
    os.makedirs(a.out, exist_ok=True)
    json.dump(top, open(f"{a.out}/{date}.json", "w"), ensure_ascii=False, indent=1)
    open(f"{a.out}/{date}.md", "w").write(digest_md(top, date, cfg))
    print(f"{len(seen)} posts found, top {len(top)} saved to {a.out}/{date}.md")

if __name__ == "__main__":
    main()
