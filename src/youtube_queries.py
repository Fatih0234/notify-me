def get_top_youtube_videos(conn, limit=5):
    """Return top YouTube videos by viral_score, split by Shorts vs long-form."""
    query = """
        SELECT v.youtube_video_id, v.title, v.is_short,
               v.view_count, v.like_count, v.comment_count,
               v.viral_score, v.viral_score_updated_at,
               c.title AS channel_name
        FROM videos v
        JOIN channels c ON v.channel_id = c.id
        WHERE v.viral_score IS NOT NULL
        ORDER BY v.is_short ASC, v.viral_score DESC
        LIMIT ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    return [dict(row) for row in cursor.fetchall()]
