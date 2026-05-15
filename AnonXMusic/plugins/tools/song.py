import html
import os
import re
import logging
import asyncio
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
    """🎵 Main song download handler - PRODUCTION READY"""
    
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
    
    file_path: Optional[str] = None
    
    try:
        logger.info(f"🔍 Searching: {query[:50]}")
        title, duration_text, duration_sec, thumb, video_id = await YouTube.details(query)
        
        if not video_id:
            await status_msg.edit_text(
                f"❌ **No results found!**\n"
                f"💡 Try:\n"
                f"• Different spelling\n"
                f"• Artist + song name\n"
                f"• Direct YouTube URL\n\n"
                f"{POWERED_BY}"
            )
            return
        
        logger.info(f"📹 Found: {title[:50]} | ID: {video_id}")
        
        # 🚀 ROBUST DOWNLOAD WITH RETRY LOGIC
        await status_msg.edit_text(f"⬇️ **Downloading MP3...**\n\n{POWERED_BY}")
        
        max_retries = 3
        download_success = False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"⬇️ Download attempt {attempt + 1}/{max_retries} for {video_id}")
                
                file_path, _ = await YouTube.download(
                    video_id, status_msg, videoid=True
                )
                
                if file_path:
                    download_success = True
                    logger.info(f"✅ Download success on attempt {attempt + 1}")
                    break
                    
            except Exception as download_err:
                logger.warning(f"⚠️ Download attempt {attempt + 1} failed: {download_err}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.5)
                    await status_msg.edit_text(
                        f"🔄 **Retrying download...**\n"
                        f"`Attempt {attempt + 2}/{max_retries}`\n\n"
                        f"{POWERED_BY}"
                    )
                else:
                    raise RuntimeError(
                        f"Download failed after {max_retries} attempts. "
                        f"API may be temporarily unavailable."
                    )
        
        if not download_success:
            raise RuntimeError("Download process did not complete")
        
        # ✅ COMPREHENSIVE FILE VALIDATION
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise RuntimeError("Downloaded file missing after validation")
        
        stat = file_path_obj.stat()
        file_size = stat.st_size
        
        if file_size < 50 * 1024:  # Minimum 50KB
            raise RuntimeError(f"File too small: {file_size / 1024:.1f} KB")
        
        if file_size > 100 * 1024 * 1024:  # Maximum 100MB
            raise RuntimeError(f"File too large: {file_size / 1024**2:.1f} MB")
        
        logger.info(f"✅ File validated: {file_size / 1024:.1f} KB")
        
        # 📱 PREPARE CAPTION
        user = message.from_user
        requester = (
            f"[{html.escape(user.first_name or 'User')}](tg://user?id={user.id})"
            if user else "Anonymous"
        )
        
        caption = (
            f"🎵 **{html.escape(title[:45])}**\n\n"
            f"⏱️ **Duration:** `{duration_text or 'LIVE'}`\n"
            f"👤 **Requested by:** {requester}\n"
            f"🎼 **Quality:** 320Kbps\n"
            f"📦 **Size:** `{file_size / 1024:.1f} KB`\n"
            f"🔗 [📺 Source](https://youtube.com/watch?v={video_id})\n\n"
            f"{POWERED_BY}"
        )
        
        # 📤 SEND AUDIO
        await status_msg.edit_text(
            f"📤 **Sending high quality MP3...**\n"
            f"`{file_size / 1024:.1f} KB`\n\n"
            f"{POWERED_BY}"
        )
        
        await app.send_audio(
            chat_id=message.chat.id,
            audio=str(file_path),
            caption=caption,
            duration=duration_sec or 0,
            title=title[:100],
            performer="BETA BOTS",
            thumb=thumb,
            reply_to_message_id=message.id
        )
        
        logger.info(f"✅ Song delivered: {title[:50]} | {file_size / 1024:.1f} KB")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Song error: {error_msg}", exc_info=True)
        
        user_friendly_msg = (
            f"❌ **Download Failed!**\n\n"
            f"```{html.escape(error_msg[:120])}```\n\n"
            f"💡 **Tips:**\n"
            f"• Try direct YouTube URL\n"
            f"• Check spelling\n"
            f"• Try later (API busy)\n\n"
            f"{POWERED_BY}"
        )
        
        await status_msg.edit_text(user_friendly_msg)
    
    finally:
        # 🧹 CLEANUP - FIXED INDENTATION
        try:
            await status_msg.delete()
        except Exception:
            pass
        
        if file_path is not None:
            try:
                path_obj = Path(file_path)
                if path_obj.exists():
                    path_obj.unlink()
                    logger.debug(f"🧹 Cleanup: {file_path}")
            except Exception as cleanup_err:
                logger.warning(f"Cleanup failed {file_path}: {cleanup_err}")


# 🔗 AUTO YOUTUBE HANDLER
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


# 📎 CAPTION HANDLER
@app.on_message(
    filters.video | filters.audio | filters.voice | filters.document
    & filters.caption & filters.regex(r"(song|music|audio)", re.IGNORECASE)
    & ~BANNED_USERS
)
@language
async def song_from_caption(client, message: Message, _):
    """📎 Song from media caption"""
    await song_download(client, message, _)
