"""
Active Chats Plugin for AnonXMusic
Shows active voice/video chats and stats
"""

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatForbidden
from unidecode import unidecode

from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils.database import (
    get_active_chats,
    get_active_video_chats,
    remove_active_chat,
    remove_active_video_chat,
)


async def generate_invite_link(chat_id: int) -> str:
    """Safely generate chat invite link"""
    try:
        invite_link = await app.export_chat_invite_link(chat_id)
        return invite_link
    except (ChatAdminRequired, UserNotParticipant, ChatForbidden):
        # Fallback to t.me/c/ link format
        chat_str = str(chat_id)
        if chat_str.startswith("-100"):
            return f"https://t.me/c/{chat_str[4:]}/1"
        return f"https://t.me/c/{chat_str[1:]}/1"
    except Exception:
        return "❌ Invite Link Unavailable"


def ordinal_number(n: int) -> str:
    """Convert integer to ordinal string (1st, 2nd, 3rd)"""
    if 10 <= (n % 100) <= 19:
        return f"{n}th"
    elif n % 10 == 1:
        return f"{n}st"
    elif n % 10 == 2:
        return f"{n}nd"
    elif n % 10 == 3:
        return f"{n}rd"
    else:
        return f"{n}th"


@app.on_message(filters.command(["activevc", "vc", "activevoice"]) & SUDOERS)
async def active_voice_chats(_, message: Message):
    """Show list of active voice chats"""
    mystic = await message.reply_text(
        "🔄 **Fetching active voice chats...**"
    )
    
    try:
        served_chats = await get_active_chats()
    except Exception as e:
        await mystic.edit_text(f"❌ **Error:** `{str(e)}`")
        return
    
    if not served_chats:
        await mystic.edit_text(
            "📭 **No active voice chats found.**"
        )
        return
    
    text = ""
    buttons = []
    j = 0
    
    for chat_id in served_chats:
        try:
            chat_info = await app.get_chat(chat_id)
            title = chat_info.title or "Unknown Chat"
            invite_link = await generate_invite_link(chat_id)
            
            # Clean title for display
            clean_title = unidecode(title)[:30]
            if len(title) > 30:
                clean_title += "..."
            
            if chat_info.username:
                text += (
                    f"**{j + 1}.** "
                    f"[{clean_title}](https://t.me/{chat_info.username}) "
                    f"`[{chat_id}]`\n"
                )
            else:
                text += (
                    f"**{j + 1}.** {clean_title} "
                    f"`[{chat_id}]`\n"
                )
            
            button_text = f"🎵 Join {ordinal_number(j + 1)} Group"
            buttons.append([InlineKeyboardButton(button_text, url=invite_link)])
            j += 1
            
        except Exception:
            # Remove invalid chats silently
            try:
                await remove_active_chat(chat_id)
            except:
                pass
            continue
    
    if not text:
        await mystic.edit_text("📭 **No valid active voice chats found.**")
        return
    
    await mystic.edit_text(
        f"**🎤 Active Voice Chats ({j}):**\n\n{text}",
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


@app.on_message(filters.command(["activevideo", "av", "activev"]) & SUDOERS)
async def active_video_chats(_, message: Message):
    """Show list of active video chats"""
    mystic = await message.reply_text(
        "🔄 **Fetching active video chats...**"
    )
    
    try:
        served_chats = await get_active_video_chats()
    except Exception as e:
        await mystic.edit_text(f"❌ **Error:** `{str(e)}`")
        return
    
    if not served_chats:
        await mystic.edit_text(
            "📭 **No active video chats found.**"
        )
        return
    
    text = ""
    buttons = []
    j = 0
    
    for chat_id in served_chats:
        try:
            chat_info = await app.get_chat(chat_id)
            title = chat_info.title or "Unknown Chat"
            invite_link = await generate_invite_link(chat_id)
            
            # Clean title for display
            clean_title = unidecode(title)[:30]
            if len(title) > 30:
                clean_title += "..."
            
            if chat_info.username:
                text += (
                    f"**{j + 1}.** "
                    f"[{clean_title}](https://t.me/{chat_info.username}) "
                    f"`[{chat_id}]`\n"
                )
            else:
                text += (
                    f"**{j + 1}.** {clean_title} "
                    f"`[{chat_id}]`\n"
                )
            
            button_text = f"🎥 Join {ordinal_number(j + 1)} Group"
            buttons.append([InlineKeyboardButton(button_text, url=invite_link)])
            j += 1
            
        except Exception:
            # Remove invalid chats silently
            try:
                await remove_active_video_chat(chat_id)
            except:
                pass
            continue
    
    if not text:
        await mystic.edit_text("📭 **No valid active video chats found.**")
        return
    
    await mystic.edit_text(
        f"**📹 Active Video Chats ({j}):**\n\n{text}",
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


@app.on_message(filters.command(["ac", "active", "stats"]) & SUDOERS)
async def active_stats(_, message: Message):
    """Show active chats statistics"""
    try:
        voice_count = len(await get_active_chats())
        video_count = len(await get_active_video_chats())
        total = voice_count + video_count
        
        stats_text = (
            f"📊 **Active Chats Stats**\n\n"
            f"🎤 **Voice Chats:** `{voice_count}`\n"
            f"📹 **Video Chats:** `{video_count}`\n"
            f"📈 **Total Active:** `{total}`\n\n"
            f"👨‍💻 **Powered by:** {app.mention}"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎤 Voice Chats", callback_data="activevc_cb"),
                InlineKeyboardButton("📹 Video Chats", callback_data="activev_cb")
            ],
            [InlineKeyboardButton("🔄 Refresh", callback_data="active_stats_cb")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
        
        await message.reply_text(
            stats_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply_text(f"❌ **Error getting stats:** `{str(e)}`")


@app.on_callback_query(filters.regex("activevc_cb") & SUDOERS)
async def cb_activevc(client, callback_query):
    """Callback for voice chats button"""
    await active_voice_chats(client, callback_query.message)


@app.on_callback_query(filters.regex("activev_cb") & SUDOERS)
async def cb_activev(client, callback_query):
    """Callback for video chats button"""
    await active_video_chats(client, callback_query.message)


@app.on_callback_query(filters.regex("active_stats_cb") & SUDOERS)
async def cb_active_stats(client, callback_query):
    """Callback for refresh stats"""
    await active_stats(client, callback_query.message)
