import sqlite3
import os
import pytest


@pytest.fixture
def twitter_fixture_db(tmp_path):
    """Create a minimal twitter.db fixture for testing."""
    db_path = tmp_path / "twitter_fixture.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE tweets (
            url TEXT PRIMARY KEY,
            username TEXT,
            text TEXT,
            posted_at TEXT,
            is_retweet INTEGER DEFAULT 0,
            is_reply INTEGER DEFAULT 0,
            is_quote_tweet INTEGER DEFAULT 0,
            is_pinned INTEGER DEFAULT 0
        );

        CREATE TABLE snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_url TEXT,
            recorded_at TEXT,
            views INTEGER,
            likes INTEGER,
            retweets INTEGER,
            replies INTEGER,
            engagement_score REAL,
            FOREIGN KEY (tweet_url) REFERENCES tweets(url)
        );

        INSERT INTO tweets VALUES
            ('https://x.com/user1/status/1', 'user1', 'Post 1 text', '2024-01-01', 0, 0, 0, 0),
            ('https://x.com/user2/status/2', 'user2', 'Post 2 text', '2024-01-01', 0, 0, 0, 0),
            ('https://x.com/user3/status/3', 'user3', 'Retweet post', '2024-01-01', 1, 0, 0, 0),
            ('https://x.com/user4/status/4', 'user4', 'Reply post', '2024-01-01', 0, 1, 0, 0),
            ('https://x.com/user5/status/5', 'user5', 'Post 3 text', '2024-01-01', 0, 0, 0, 0),
            ('https://x.com/user6/status/6', 'user6', 'Post 4 text', '2024-01-01', 0, 0, 0, 0),
            ('https://x.com/user7/status/7', 'user7', 'Post 5 text', '2024-01-01', 0, 0, 0, 0);

        INSERT INTO snapshots (tweet_url, recorded_at, views, likes, retweets, replies, engagement_score) VALUES
            ('https://x.com/user1/status/1', '2024-01-01T10:00:00', 1000, 100, 50, 20, 9.5),
            ('https://x.com/user1/status/1', '2024-01-01T12:00:00', 2000, 200, 80, 40, 12.0),
            ('https://x.com/user2/status/2', '2024-01-01T10:00:00', 500, 80, 20, 10, 7.5),
            ('https://x.com/user3/status/3', '2024-01-01T10:00:00', 3000, 300, 100, 50, 15.0),
            ('https://x.com/user4/status/4', '2024-01-01T10:00:00', 2500, 250, 90, 45, 13.5),
            ('https://x.com/user5/status/5', '2024-01-01T10:00:00', 800, 60, 15, 8, 5.0),
            ('https://x.com/user6/status/6', '2024-01-01T10:00:00', 600, 40, 10, 5, 4.0),
            ('https://x.com/user7/status/7', '2024-01-01T10:00:00', 400, 20, 5, 3, 3.0);
    """)
    conn.commit()
    conn.close()
    return str(db_path)


@pytest.fixture
def yt_fixture_db(tmp_path):
    """Create a minimal youtube_competitor_tracker.db fixture for testing."""
    db_path = tmp_path / "yt_fixture.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE channels (
            id INTEGER PRIMARY KEY,
            title TEXT,
            handle TEXT
        );

        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_video_id TEXT,
            channel_id INTEGER,
            title TEXT,
            duration_seconds INTEGER,
            is_short INTEGER DEFAULT 0,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            published_at TEXT,
            FOREIGN KEY (channel_id) REFERENCES channels(id)
        );

        INSERT INTO channels VALUES
            (1, 'TechChannel', '@tech'),
            (2, 'FunChannel', '@fun'),
            (3, 'NewsChannel', '@news');

        INSERT INTO videos (youtube_video_id, channel_id, title, duration_seconds, is_short, view_count, like_count, comment_count, published_at) VALUES
            ('vid1', 1, 'Top Tech Trends 2024', 600, 0, 100000, 5000, 800, '2024-01-01'),
            ('vid2', 2, 'Funny Shorts Compilation', 45, 1, 500000, 10000, 2000, '2024-01-02'),
            ('vid3', 3, 'Breaking News Today', 300, 0, 200000, 3000, 500, '2024-01-03'),
            ('vid4', 1, 'Python Tutorial', 1200, 0, 50000, 4000, 600, '2024-01-04'),
            ('vid5', 2, 'Comedy Sketch', 180, 0, 80000, 6000, 1200, '2024-01-05'),
            ('vid6', 3, 'Daily Vlog', 900, 0, 30000, 1000, 200, '2024-01-06');
    """)
    conn.commit()
    conn.close()
    return str(db_path)
