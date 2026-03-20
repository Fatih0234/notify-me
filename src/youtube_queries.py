def get_top_youtube_videos(conn, limit=5):
    """Return top YouTube videos by computed viral score."""
    query = """
        SELECT v.youtube_video_id, v.title, v.is_short,
               v.view_count, v.like_count, v.comment_count,
               c.title AS channel_name,
               (v.like_count + v.comment_count * 2.0) / MAX(v.view_count, 1) AS viral_score
        FROM videos v
        JOIN channels c ON v.channel_id = c.id
        ORDER BY viral_score DESC
        LIMIT ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    return [dict(row) for row in cursor.fetchall()]
