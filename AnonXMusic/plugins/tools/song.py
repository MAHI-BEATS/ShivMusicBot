import html
import os
import re
from typing import Optional, Tuple

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType

from AnonXMusic import YouTube, app
from AnonXMusic.utils.decorators.language import language
from config import BANNED_USERS


def extract_song_query(message: Message) -> str:
    """Extract song query from message"""
    # Command query
    if message.command and len(message.command) > 1:
        return " ".join(message.command[1:]).strip()
    
    # Reply query
    if message.reply_to_message:
        text = (
            message.reply_to_message.text 
            or message.reply_to_message.caption 
            or ""
        )
        return text.strip()
    
    # Direct media caption
    if message.caption:
        return message.caption.strip()
    
    return ""


def is_playlist(url: str) -> bool:
    """Check if URL is a playlist"""
    playlist_patterns = [
        r"playlist\?list=",
        r"/playlist\?",
        r"list=PL"
    ]
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in playlist_patterns)


@app.on_message(
    filters.command(["song", "music", "audio"]) 
    & ~BANNED_USERS
)
@language
async def song_download(client: app, message: Message, _):
    """Main song download handler"""
    
    # Extract query
    query = (await YouTube.url(message)) or extract_song_query(message)
    
    if not query:
        await message.reply_text(
            "**Usage:**\n"
            "• `/song <song name>`\n"
            "• `/song <YouTube URL>`\n"
            "• Reply to message with `/song`",
            quote=True
        )
        return
    
    # Check for playlists
    if is_playlist(query):
        await message.reply_text(
            "❌ **Playlists not supported!**\n"
            "Please send a **single YouTube track** or **search query**.",
            quote=True
        )
        return
    
    # Send status message
    status_msg = await message.reply_text(
        "🔍 **Searching...BY BETA BOTS.🙂❤️...**",
        quote=True
    )
    
    try:
        # Get YouTube details
        title, duration_text, duration_sec, thumb, video_id = await YouTube.details(query)
        
        if not video_id:
            await status_msg.edit_text("❌ **No results found!**")
            return
        
        await status_msg.edit_text("⬇️ **Downloading MP3...BY BETA BOTS.🙂❤️...**")
        
        # Download audio
        file_path, direct = await YouTube.download(
            video_id, 
            status_msg, 
            videoid=True
        )
        
        if not os.path.exists(file_path):
            raise RuntimeError("Audio file not found after download")
        
        # Prepare caption
        user = message.from_user
        requested_by = (
            f"[{user.first_name}](tg://user?id={user.id})"
            if user 
            else "Unknown User"
        )
        
        caption = (
            f"🎵 **Title:** {html.escape(title[:50])}\n"
            f"⏱️ **Duration:** {duration_text or 'Unknown'}\n"
            f"👤 **Requested by:** {requested_by}\n"
            f"🔗 **[YouTube](https://youtube.com/watch?v={video_id})**"
        )
        
        await status_msg.edit_text("📤 **Uploading MP3...BY BETA BOTS.🙂❤️...**")
        
        # Send audio
        await app.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            caption=caption,
            duration=duration_sec,
            title=title[:100],
            performer="AnonXMusic",
            thumb=thumb,
            reply_to_message_id=message.id
        )
        
        # Cleanup
        await status_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as exc:
        error_msg = str(exc)
        await status_msg.edit_text(
            f"❌ **Download Failed!**\n"
            f"`{html.escape(error_msg[:100])}`",
            quote=True
        )


@app.on_message(
    filters.regex(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/.+")
    & ~filters.command(["song", "music", "audio"])
    & ~BANNED_USERS
)
@language
async def auto_song_from_url(client: app, message: Message, _):
    """Auto-download from YouTube URLs"""
    if message.reply_to_message or message.media:
        return  # Don't interfere with other handlers
    
    await song_download(client, message, _)
