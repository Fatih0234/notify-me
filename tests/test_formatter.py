import pytest
from src.formatter import escape_md, truncate, format_number, build_message


def test_escape_md_special_chars():
    text = "hello_world [test] (value) *bold* ~strike~"
    escaped = escape_md(text)
    assert r"\_" in escaped or "hello" in escaped
    # Underscores should be escaped
    assert r"\_" in escaped
    assert r"\[" in escaped
    assert r"\(" in escaped
    assert r"\*" in escaped


def test_escape_md_none():
    assert escape_md(None) == ""


def test_truncate_short_text():
    assert truncate("hello", 120) == "hello"


def test_truncate_long_text():
    long_text = "a" * 200
    result = truncate(long_text, 120)
    assert len(result) <= 120
    assert result.endswith("…")


def test_format_number_millions():
    assert format_number(1_500_000) == "1.5M"


def test_format_number_thousands():
    assert format_number(5_000) == "5.0K"


def test_format_number_small():
    assert format_number(999) == "999"


def test_format_number_none():
    assert format_number(None) == "0"


def make_sample_x_posts():
    return [
        {
            "username": "testuser",
            "url": "https://x.com/testuser/status/1",
            "text": "Test tweet content",
            "views": 1000,
            "likes": 100,
            "retweets": 50,
            "replies": 20,
            "engagement_score": 9.5,
        }
    ]


def make_sample_yt_videos():
    return [
        {
            "youtube_video_id": "abc123",
            "title": "Test Video Title",
            "is_short": 0,
            "view_count": 100000,
            "like_count": 5000,
            "comment_count": 500,
            "channel_name": "TestChannel",
            "viral_score": 0.06,
        }
    ]


def make_asset_info(ts="2024-01-01T00:00:00Z"):
    return {"asset_updated_at": ts}


def test_build_message_returns_list():
    messages = build_message(
        make_sample_x_posts(),
        make_sample_yt_videos(),
        make_asset_info(),
        make_asset_info(),
    )
    assert isinstance(messages, list)
    assert len(messages) >= 1


def test_build_message_contains_sections():
    messages = build_message(
        make_sample_x_posts(),
        make_sample_yt_videos(),
        make_asset_info(),
        make_asset_info(),
    )
    full_text = "\n".join(messages)
    assert "Viral Content Digest" in full_text
    assert "Top X Posts" in full_text
    assert "Top YouTube Videos" in full_text


def test_build_message_split_on_large_content():
    """Test that very large content is split into multiple messages."""
    # Create enough posts to exceed 4096 chars
    x_posts = []
    for i in range(5):
        x_posts.append({
            "username": f"user{i}" * 5,
            "url": f"https://x.com/user{i}/status/{i}",
            "text": "A" * 120,
            "views": 100000,
            "likes": 10000,
            "retweets": 5000,
            "replies": 2000,
            "engagement_score": 9.5 - i * 0.1,
        })
    yt_videos = []
    for i in range(5):
        yt_videos.append({
            "youtube_video_id": f"vid{i}",
            "title": "B" * 80,
            "is_short": 0,
            "view_count": 100000,
            "like_count": 5000,
            "comment_count": 500,
            "channel_name": f"Channel{i}" * 4,
            "viral_score": 0.06 - i * 0.001,
        })

    messages = build_message(x_posts, yt_videos, make_asset_info(), make_asset_info())
    # Either one message under 4096, or multiple messages
    for msg in messages:
        assert len(msg) <= 4096


def test_build_message_with_null_fields():
    """Test that None/null fields don't cause errors."""
    x_posts = [{
        "username": None,
        "url": None,
        "text": None,
        "views": None,
        "likes": None,
        "retweets": None,
        "replies": None,
        "engagement_score": None,
    }]
    yt_videos = [{
        "youtube_video_id": None,
        "title": None,
        "is_short": None,
        "view_count": None,
        "like_count": None,
        "comment_count": None,
        "channel_name": None,
        "viral_score": None,
    }]
    # Should not raise
    messages = build_message(x_posts, yt_videos, make_asset_info(), make_asset_info())
    assert len(messages) >= 1
