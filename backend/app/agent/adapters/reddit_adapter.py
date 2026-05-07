from __future__ import annotations

from typing import Any, Iterable


class RedditAdapter:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None, username: str | None = None, password: str | None = None) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self._reddit: Any = None
        self._connect()

    def _connect(self) -> None:
        if not (self.client_id and self.client_secret):
            return
        try:
            import praw
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent="PRISM/2.0",
            )
        except Exception:
            self._reddit = None

    def available(self) -> bool:
        return self._reddit is not None

    def monitor_subreddits(self, subreddits: list[str] | None = None, min_score: int = 50) -> Iterable[dict[str, Any]]:
        if not self.available():
            return []
        names = subreddits or ["MachineLearning", "LocalLLaMA", "artificial"]
        posts = self._reddit.subreddit("+".join(names)).hot(limit=25)
        return [
            {"title": post.title, "url": post.url, "score": post.score, "source": "reddit"}
            for post in posts
            if post.score >= min_score
        ]
