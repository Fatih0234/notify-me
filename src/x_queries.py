def get_top_x_posts(conn, limit=5):
    """Return top X posts by viral_score from latest snapshot."""
    query = """
        SELECT t.username, t.url, t.text,
               s.views, s.likes, s.retweets, s.replies,
               s.viral_score, s.view_momentum, s.engagement_momentum,
               s.quality, s.freshness
        FROM tweets t
        JOIN snapshots s ON t.url = s.tweet_url
        WHERE s.id IN (SELECT MAX(id) FROM snapshots GROUP BY tweet_url)
          AND t.is_retweet = 0
          AND t.is_reply   = 0
          AND t.is_pinned  = 0
        ORDER BY s.viral_score DESC
        LIMIT ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    return [dict(row) for row in cursor.fetchall()]
