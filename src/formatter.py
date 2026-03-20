import re
from datetime import datetime, timezone


def escape_md(text):
    """Escape special characters for Telegram MarkdownV2."""
    if text is None:
        return ""
    special = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(r"([" + re.escape(special) + r"])", r"\\\1", str(text))


def truncate(text, max_len):
    """Truncate text to max_len chars, adding ellipsis if needed."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def format_number(n):
    """Format large numbers with K/M suffixes."""
    if n is None:
        return "0"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def build_message(x_posts, yt_videos, x_asset_info, yt_asset_info):
    """Build Telegram MarkdownV2 message(s). Returns list of message strings."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append(f"*🔥 Viral Content Digest*")
    lines.append(f"_{escape_md(now_str)}_")
    lines.append("")

    # X / Twitter section
    lines.append("*📊 Top X Posts*")
    lines.append("")
    for i, post in enumerate(x_posts, 1):
        username = escape_md(post.get("username", "unknown"))
        url = post.get("url", "")
        text = escape_md(truncate(post.get("text", ""), 120))
        views = format_number(post.get("views"))
        likes = format_number(post.get("likes"))
        replies = format_number(post.get("replies"))
        rts = format_number(post.get("retweets"))
        score = post.get("viral_score")
        score_str = escape_md(f"{score:.4f}" if score is not None else "N/A")
        view_mom = post.get("view_momentum")
        eng_mom = post.get("engagement_momentum")
        freshness = post.get("freshness")
        view_mom_str = escape_md(f"{view_mom:.1f}/h" if view_mom is not None else "N/A")
        eng_mom_str = escape_md(f"{eng_mom:.1f}/h" if eng_mom is not None else "N/A")
        freshness_str = escape_md(f"{freshness:.2f}" if freshness is not None else "N/A")

        lines.append(f"*{i}\\. @{username}*")
        lines.append(text)
        lines.append(
            f"👁 {escape_md(views)} · ❤️ {escape_md(likes)} · 💬 {escape_md(replies)} · 🔁 {escape_md(rts)}"
        )
        lines.append(
            f"📈 {view_mom_str} views · ⚡ {eng_mom_str} eng · 🌱 freshness {freshness_str}"
        )
        lines.append(f"Viral score: `{score_str}`")
        if url:
            lines.append(f"[View tweet]({url})")
        lines.append("")

    # YouTube section — long-form and Shorts rendered separately
    long_form = [v for v in yt_videos if not v.get("is_short")]
    shorts = [v for v in yt_videos if v.get("is_short")]

    def render_yt_video(i, video):
        vid_id = video.get("youtube_video_id", "")
        title = escape_md(truncate(video.get("title", ""), 80))
        channel = escape_md(video.get("channel_name", "Unknown"))
        views = format_number(video.get("view_count"))
        likes = format_number(video.get("like_count"))
        comments = format_number(video.get("comment_count"))
        score = video.get("viral_score")
        score_str = escape_md(f"{score:.4f}" if score is not None else "N/A")
        yt_url = f"https://youtube.com/watch?v={vid_id}" if vid_id else ""

        out = []
        out.append(f"*{i}\\. {channel}*")
        out.append(title)
        out.append(
            f"👁 {escape_md(views)} · ❤️ {escape_md(likes)} · 💬 {escape_md(comments)}"
        )
        out.append(f"Viral score: `{score_str}`")
        if yt_url:
            out.append(f"[Watch]({yt_url})")
        out.append("")
        return out

    lines.append("*📺 Top YouTube Videos*")
    lines.append("")
    for i, video in enumerate(long_form, 1):
        lines.extend(render_yt_video(i, video))

    if shorts:
        lines.append("*🩳 Top YouTube Shorts*")
        lines.append("")
        for i, video in enumerate(shorts, 1):
            lines.extend(render_yt_video(i, video))

    # Footer
    x_ts = escape_md(x_asset_info.get("asset_updated_at", "N/A"))
    yt_ts = escape_md(yt_asset_info.get("asset_updated_at", "N/A"))
    lines.append("─────────────────")
    lines.append(f"X data: _{x_ts}_")
    lines.append(f"YT data: _{yt_ts}_")

    full_message = "\n".join(lines)

    # Split if > 4096 chars
    if len(full_message) <= 4096:
        return [full_message]

    # Split into two: X section and YT section
    split_marker = "*📺 Top YouTube Videos*"
    idx = full_message.find(split_marker)
    if idx == -1:
        # Can't find split point, return as-is (truncated)
        return [full_message[:4096]]

    msg1 = full_message[:idx].rstrip()
    msg2 = full_message[idx:]

    # Add footer to msg2 only (it's already there)
    # Remove trailing footer from msg1 if it got split before
    return [msg1, msg2]
