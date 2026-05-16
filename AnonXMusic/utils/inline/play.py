import math
import random

from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton

from AnonXMusic import app  # ✅ NameError fixed
from AnonXMusic.utils.formatters import time_to_seconds

# 🔥 PREMIUM EMOJIS LIST 🔥
PREMIUM_EMOJIS = [
    "5422831825178206894", 
    "5368324170673489600",
    "5206607081334906820",
    "5206380668048496464"
]

# 🎨 Dynamic Color Generator
def get_style_map():
    styles = [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]
    random.shuffle(styles)
    # ✅ KeyErrors protection with safe fallback mapping
    return {
        1: styles[0], 
        2: styles[1], 
        3: styles[2], 
        5: styles[0]
    }

# 🔘 Smart Button Creator
def create_btn(text, cb=None, url=None, style=ButtonStyle.PRIMARY, no_emoji=False):
    kwargs = {"text": text, "style": style}
    if cb: kwargs["callback_data"] = cb
    if url: kwargs["url"] = url
    if not no_emoji: kwargs["icon_custom_emoji_id"] = random.choice(PREMIUM_EMOJIS)
    return InlineKeyboardButton(**kwargs)


def track_markup(_, videoid, user_id, channel, fplay):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(_["P_B_1"], cb=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style=s_map.get(2)),
            create_btn(_["P_B_2"], cb=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style=s_map.get(2)),
        ],
        [
            create_btn(_["CLOSE_BUTTON"], cb=f"forceclose {videoid}|{user_id}", style=s_map.get(1))
        ],
    ]
    return buttons


def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100 if duration_sec > 0 else 0
    umm = math.floor(percentage)
    
    if 0 < umm <= 10: bar = "◉—————————"
    elif 10 < umm < 20: bar = "—◉————————"
    elif 20 <= umm < 30: bar = "——◉———————"
    elif 30 <= umm < 40: bar = "———◉——————"
    elif 40 <= umm < 50: bar = "————◉—————"
    elif 50 <= umm < 60: bar = "—————◉————"
    elif 60 <= umm < 70: bar = "——————◉———"
    elif 70 <= umm < 80: bar = "———————◉--"
    elif 80 <= umm < 95: bar = "————————◉—"
    else: bar = "—————————◉"
    
    s_map = get_style_map()
    buttons = [
        [
            # Progress bar
            create_btn(f"{played} {bar} {dur}", cb="GetTimer", style=s_map.get(1), no_emoji=True)
        ],
        [   
            # Media controls 
            create_btn("▷", cb=f"ADMIN Resume|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("II", cb=f"ADMIN Pause|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("↻", cb=f"ADMIN Replay|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("‣‣I", cb=f"ADMIN Skip|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("▢", cb=f"ADMIN Stop|{chat_id}", style=s_map.get(5), no_emoji=True),
        ],
        [
            create_btn(
                text=_["S_B_3"], 
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map.get(1)
            )      
        ],
        [
            create_btn(text=_["CLOSE_BUTTON"], cb="close", style=s_map.get(1))
        ],
    ]
    return buttons


def stream_markup(_, chat_id):
    s_map = get_style_map()
    buttons = [
        [
            create_btn("▷", cb=f"ADMIN Resume|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("II", cb=f"ADMIN Pause|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("↻", cb=f"ADMIN Replay|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("‣‣I", cb=f"ADMIN Skip|{chat_id}", style=s_map.get(5), no_emoji=True),
            create_btn("▢", cb=f"ADMIN Stop|{chat_id}", style=s_map.get(5), no_emoji=True),
        ],
        [
            create_btn(
                text=_["S_B_3"], 
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map.get(1)
            )      
        ],
        [
            create_btn(text=_["CLOSE_BUTTON"], cb="close", style=s_map.get(1))
        ],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(_["P_B_1"], cb=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}", style=s_map.get(2)),
            create_btn(_["P_B_2"], cb=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}", style=s_map.get(2)),
        ],
        [
            create_btn(_["CLOSE_BUTTON"], cb=f"forceclose {videoid}|{user_id}", style=s_map.get(1)),
        ],
        [
            create_btn(
                text=_["S_B_3"], 
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map.get(1)
            )      
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(_["P_B_3"], cb=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}", style=s_map.get(1)),
        ],
        [
            create_btn(_["CLOSE_BUTTON"], cb=f"forceclose {videoid}|{user_id}", style=s_map.get(1)),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    s_map = get_style_map()
    buttons = [
        [
            create_btn(_["P_B_1"], cb=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style=s_map.get(2)),
            create_btn(_["P_B_2"], cb=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style=s_map.get(2)),
        ],
        [
            create_btn("◁", cb=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=s_map.get(3), no_emoji=True),
            create_btn(_["CLOSE_BUTTON"], cb=f"forceclose {query}|{user_id}", style=s_map.get(3)),
            create_btn("▷", cb=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=s_map.get(3), no_emoji=True),
        ],
        [
            create_btn(
                text=_["S_B_3"], 
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map.get(1)
            )      
        ],
    ]
    return buttons


def queue_markup(_, videoid, chat_id):  # ✅ Checked and verified clear argument structure
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text=_["S_B_3"], 
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map.get(1)
            )      
        ],
    ]
    return buttons
