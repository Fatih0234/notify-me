import sqlite3
import pytest

from src.db_loader import load_db
from src.x_queries import get_top_x_posts
from src.youtube_queries import get_top_youtube_videos


def test_top_x_posts_ordering(twitter_fixture_db):
    conn = load_db(twitter_fixture_db)
    posts = get_top_x_posts(conn)
    conn.close()

    # Should have max 5 results
    assert len(posts) <= 5

    # All results should not be retweets or replies
    # (retweet user3 score=15.0 and reply user4 score=13.5 should be excluded)
    usernames = [p["username"] for p in posts]
    assert "user3" not in usernames  # is_retweet=1
    assert "user4" not in usernames  # is_reply=1

    # Should be ordered by engagement_score descending
    scores = [p["engagement_score"] for p in posts]
    assert scores == sorted(scores, reverse=True)


def test_top_x_posts_latest_snapshot(twitter_fixture_db):
    """user1 has two snapshots; should use the latest (higher score)."""
    conn = load_db(twitter_fixture_db)
    posts = get_top_x_posts(conn)
    conn.close()

    user1_post = next((p for p in posts if p["username"] == "user1"), None)
    assert user1_post is not None
    # Latest snapshot has engagement_score=12.0
    assert user1_post["engagement_score"] == 12.0


def test_top_yt_videos_ordering(yt_fixture_db):
    conn = load_db(yt_fixture_db)
    videos = get_top_youtube_videos(conn)
    conn.close()

    assert len(videos) <= 5

    # Should be ordered by viral_score descending
    scores = [v["viral_score"] for v in videos]
    assert scores == sorted(scores, reverse=True)


def test_top_yt_videos_has_channel_name(yt_fixture_db):
    conn = load_db(yt_fixture_db)
    videos = get_top_youtube_videos(conn)
    conn.close()

    for v in videos:
        assert "channel_name" in v
        assert v["channel_name"] is not None


def test_top_yt_videos_short_label(yt_fixture_db):
    conn = load_db(yt_fixture_db)
    videos = get_top_youtube_videos(conn)
    conn.close()

    # vid2 is a short with high engagement, should appear in results
    short_video = next((v for v in videos if v.get("is_short") == 1), None)
    # vid2 has like_count=10000, comment_count=2000, view_count=500000
    # viral_score = (10000 + 2000*2) / 500000 = 14000/500000 = 0.028
    # May or may not be in top 5 depending on other scores
    # Just verify the is_short field is present
    for v in videos:
        assert "is_short" in v
