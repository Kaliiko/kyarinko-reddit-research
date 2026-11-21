# kyarinko-reddit-research

A small, read-only Python script I run once a week on my own laptop. It's the only thing that uses my Reddit API access.

It searches about 10 music and art subreddits for public posts from the past week about beginner problems: not finishing songs, getting no listeners, pricing a first commission. Then it saves the top 40 to a private local file. I use that to pick topics for my own educational short videos for beginner musicians and artists.

- **Read-only.** It doesn't post, vote, comment, message or moderate.
- **Small.** One run a week, about 170 search requests spaced 1.2 s apart (about 4 minutes).
- **Stores very little:** title, first 500 characters of text, score, comment count, date, link. No usernames, no comments, no profiles, nothing from NSFW posts.
- **Not shared.** Results stay on my machine. I don't quote posts or show usernames in videos, sell the data, or use it to train AI or ML models.
- **Auth:** application-only OAuth (`client_credentials`) with a descriptive User-Agent. Keys live in `~/.config/kyarinko/reddit.json`, never in this repo.

## Run
```
python3 reddit_scan.py            # uses config.json, writes scans/YYYY-MM-DD.md + .json
```
Standard library only, no dependencies.

Made by Kyarinko, an independent musician: https://kyarinko.online
