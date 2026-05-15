import html
import os
import re
import logging
from typing import Optional, Tuple
from pathlib import Path

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType

from AnonXMusic import YouTube, app
from AnonXMusic.utils.decorators.language import language
from config import BANNED_USERS

logger = logging.getLogger(__name__)

POWERED_BY = "🤞 **𝐏ᴏᴡєʀєᴅ 𝐁ʏ ➛ BETA BOTS.🙂❤️**"

def extract_song_query(message: Message) -> str:
    """Extract song query from message/command/reply"""
    if message.command and len(message.command) > 1:
        return " ".join(message.command[1:]).strip()
    
    if message.reply_to_message:
        return (
            message.reply_to_message.text 
            or message.reply_to_message.caption 
            or ""
        ).strip()
    
    if message.caption:
        return message.caption.strip()
    
    return ""

def is_playlist(url: str) -> bool:
    """Detect YouTube playlists"""
    patterns = [
        r"playlist\?list=",
        r"/playlist\?",
        r"list=PL",
        r"playlist/"
    ]
    return bool(re.search("|".join(patterns), url, re.IGNORECASE))

@app.on_message(
    filters.command(["song", "music", "audio", "mp3"]) 
    & ~BANNED_USERS
)
@language
async def song_download(client, message: Message, _):
    """🎵 Main song download handler"""
    
    query = (await YouTube.url(message)) or extract_song_query(message)
    
    if not query:
        await message.reply_text(
            f"**🎵 Song Downloader**\n\n"
            f"**Commands:**\n"
            f"• `.song <song name>`\n"
            f"• `.song <YouTube URL>`\n"
            f"• Reply + `.song`\n\n"
            f"**Example:**\n"
            f"`.song kesariya`\n\n"
            f"{POWERED_BY}",
            quote=True
        )
        return
    
    if is_playlist(query):
        await message.reply_text(
            f"❌ **Playlists not supported**\n\n"
            f"📎 Send **single track URL** or **song name** only!\n\n"
            f"{POWERED_BY}",
            quote=True
        )
        return
    
    status_msg = await message.reply_text(
        f"🔍 **Searching your song...**\n\n{POWERED_BY}"
    )
    
    file_path: Optional[str] = None  # ✅ Explicitly typed and initialized
    
    try:
        logger.info(f"Searching: {query[:50]}")
        title, duration_text, duration_sec, thumb, video_id = await YouTube.details(query)
        
        if not video_id:
            await status_msg.edit_text(
                f"❌ **No results found!**\nTry different song name.\n\n{POWERED_BY}"
            )
            return
        
        await status_msg.edit_text(
            f"⬇️ **Downloading MP3...**\n\n{POWERED_BY}"
        )
        
        # ✅ Download might return None - handle gracefully
        file_path, _ = await YouTube.download(
            video_id, status_msg, videoid=True
        )
        
        # ✅ Comprehensive file validation
        if not file_path:
            raise RuntimeError("Download returned None path")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists() or not file_path_obj.is_file():
            raise RuntimeError(f"Downloaded file not found: {file_path}")
        
        # ✅ Verify file size (basic sanity check)
        if file_path_obj.stat().st_size == 0:
            raise RuntimeError("Downloaded empty file")
        
        user = message.from_user
        requester = (
            f"[{html.escape(user.first_name or user.first_name)}](tg://user?id={user.id})"
            if user else "Anonymous"
        )
        
        caption = (
            f"🎵 **{html.escape(title[:45])}**\n\n"
            f"⏱️ **Duration:** `{duration_text or 'LIVE'}`\n"
            f"👤 **Requested by:** {requester}\n"
            f"🎼 **Quality:** 320Kbps\n"
            f"🔗 [📺 Source](https://youtube.com/watch?v={video_id})\n\n"
            f"{POWERED_BY}"
        )
        
        await status_msg.edit_text(
            f"📤 **Sending high quality MP3...**\n\n{POWERED_BY}"
        )
        
        await app.send_audio(
            chat_id=message.chat.id,
            audio=str(file_path),  # ✅ Ensure string
            caption=caption,
            duration=duration_sec or 0,
            title=title[:100],
            performer="BETA BOTS",
            thumb=thumb,
            reply_to_message_id=message.id,
            progress_callback=lambda current, total: None  # Optional
        )
        
        logger.info(f"✅ Song sent successfully: {title[:50]}")
        
    except Exception as e:
        logger.error(f"Song download error: {str(e)}", exc_info=True)
        await status_msg.edit_text(
            f"❌ **Download Failed!**\n\n"
            f"```{html.escape(str(e)[:100])}```\n\n"
            f"{POWERED_BY}"
        )
    
    finally:
        # ✅ Safe status message cleanup
        try:
            await status_msg.delete()
        except:
            pass
        
        # ✅ FIXED - Safe file cleanup (THIS WAS THE CRASHING PART)
        if file_path is not None:
            file_path_obj = Path(file_path)
            if file_path_obj.exists() and file_path_obj.is_file():
                try:
                    file_path_obj.unlink()
                    logger.debug(f"✅ Temporary file cleaned up: {file_path}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to cleanup {file_path}: {cleanup_err}")


@app.on_message(
    filters.regex(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be|music\.youtube\.com)/.+")
    & ~filters.command(["song", "music", "audio", "mp3"])
    & ~BANNED_USERS
)
@language
async def auto_youtube_song(client, message: Message, _):
    """🔗 Auto-download from YouTube URLs"""
    if message.reply_to_message or message.media:
        return
    await song_download(client, message, _)


@app.on_message(
    filters.video | filters.audio | filters.voice | filters.document
    & filters.caption & filters.regex(r"(song|music|audio)")
    & ~BANNED_USERS
)
@language
async def song_from_caption(client, message: Message, _):
    """📎 Song from media caption"""
    await song_download(client, message, _)
