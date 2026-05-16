import os
import re
import random
import aiofiles
import aiohttp
from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageOps,
)
from unidecode import unidecode
from ytSearch import VideosSearch

from AnonXMusic import app
from config import YOUTUBE_IMG_URL

# --- Helper Functions ---

def changeImageSize(maxWidth, maxHeight, image):
    image = image.copy()
    image.thumbnail((maxWidth, maxHeight))
    return image

def circle(img):
    img = img.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output

def clear(text, max_length=45):
    """Shortens the text and adds '...' if it exceeds max_length."""
    text = text.strip()
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    return text

def rounded_rectangle_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask

def add_raindrops(image, count=100):
    """Procedurally generates raindrop highlights and shadows for a wet glass effect."""
    draw = ImageDraw.Draw(image)
    w, h = image.size
    for _ in range(count):
        # Random position and size
        x = random.randint(10, w - 10)
        y = random.randint(10, h - 10)
        r = random.randint(2, 5)
        
        # Draw droplet shadow
        draw.ellipse((x+1, y+1, x+r+1, y+r+1), fill=(0, 0, 0, 50))
        # Draw droplet highlight
        draw.ellipse((x, y, x+r, y+r), fill=(255, 255, 255, 100))
    return image

def create_glass_panel(base_img, box, radius=60, blur=15, alpha=80):
    x1, y1, x2, y2 = box
    crop = base_img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur))
    
    # Base dark overlay
    overlay = Image.new("RGBA", crop.size, (10, 15, 30, alpha))
    glass = Image.alpha_composite(crop.convert("RGBA"), overlay)
    
    # Add Raindrop Effect
    glass = add_raindrops(glass, count=150)
    
    mask = rounded_rectangle_mask(glass.size, radius)
    final = Image.new("RGBA", glass.size, (0, 0, 0, 0))
    final.paste(glass, (0, 0), mask)
    return final

def add_neon_glow(image, glow_color=(0, 255, 255), blur_radius=25, expand=40):
    base = image.convert("RGBA")
    w, h = base.size
    alpha = base.split()[-1]
    glow = Image.new("RGBA", (w + expand * 2, h + expand * 2), (0, 0, 0, 0))
    glow_mask = Image.new("L", (w + expand * 2, h + expand * 2), 0)
    glow_mask.paste(alpha, (expand, expand))
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(blur_radius))
    color_layer = Image.new("RGBA", glow.size, glow_color + (180,))
    glow.paste(color_layer, (0, 0), glow_mask)
    glow.paste(base, (expand, expand), base)
    return glow

def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    x, y = position
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=fill)

async def download_user_photo(user_id: int):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except:
        pass
    return None

# --- Main Thumbnail Function ---

async def get_thumb(videoid, user_id):
    os.makedirs("cache", exist_ok=True)
    final_path = f"cache/{videoid}_{user_id}.png"

    if os.path.isfile(final_path):
        return final_path

    url = f"https://www.youtube.com/watch?v={videoid}"

    try:
        results = VideosSearch(url, limit=1)
        data = await results.next()
        result = data["result"][0]

        title = re.sub(r"\W+", " ", result["title"]).title()
        duration = result.get("duration", "00:00")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown")
        channel = result.get("channel", {}).get("name", "Unknown Artist")

        thumb_path = f"cache/thumb_{videoid}.png"
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, mode="wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL

        # Canvas setup
        bg_image = Image.open(thumb_path).convert("RGBA")
        background = bg_image.resize((1920, 1080)).filter(ImageFilter.GaussianBlur(25))
        background = ImageEnhance.Brightness(background).enhance(0.35)

        draw = ImageDraw.Draw(background)
        
        # 1. Main UI Card (Glass Panel with Raindrops)
        panel_box = (50, 50, 1870, 1030)
        glass = create_glass_panel(background, panel_box, radius=60, blur=20, alpha=90)
        background.paste(glass, (panel_box[0], panel_box[1]), glass)
        # Card Border
        draw.rounded_rectangle(panel_box, radius=60, outline=(132, 224, 240, 180), width=6)

        # 2. Fonts - Added error handling for missing fonts
        try:
            font_path = "AnonXMusic/assets/font.ttf"
            font_path2 = "AnonXMusic/assets/font2.ttf"
            title_font = ImageFont.truetype(font_path, 68)
            heading_font = ImageFont.truetype(font_path2, 48)
            small_font = ImageFont.truetype(font_path2, 38)
            branding_font = ImageFont.truetype(font_path2, 55)
        except:
            # Fallback fonts
            title_font = ImageFont.load_default()
            heading_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            branding_font = ImageFont.load_default()

        # 3. Left Thumbnail (Circular)
        yt_circle = circle(bg_image)
        yt_circle = changeImageSize(550, 550, yt_circle)
        yt_glow = add_neon_glow(yt_circle, glow_color=(255, 60, 160), blur_radius=30, expand=45)
        background.paste(yt_glow, (100, 230), yt_glow)

        # 4. User Profile
        user_photo_path = await download_user_photo(user_id)
        if user_photo_path and os.path.exists(user_photo_path):
            try:
                u_img = Image.open(user_photo_path).convert("RGBA")
                u_circle = circle(u_img)
                u_circle = changeImageSize(380, 380, u_circle)
                u_glow = add_neon_glow(u_circle, glow_color=(0, 255, 255), blur_radius=30, expand=45)
                background.paste(u_glow, (1410, 310), u_glow)
            except:
                pass  # Skip user photo if there's any error

        # 5. Text Elements
        bot_name = getattr(app, 'name', 'ANONXMUSIC')
        draw_text_with_glow(draw, (90, 85), f"{unidecode(bot_name).upper()}", heading_font, (132, 224, 240), (132, 224, 240, 100))
        draw_text_with_glow(draw, (1500, 85), "NOW PLAYING", heading_font, (132, 224, 240), (132, 224, 240, 100))

        # Using the new clear() function to format the title
        draw.text((750, 320), clear(title, max_length=45), fill="white", font=title_font)
        draw.text((750, 430), f"Artist: {channel}", fill=(220, 220, 220), font=small_font)
        draw.text((750, 490), f"Views: {views}", fill=(190, 190, 190), font=small_font)
        draw.text((750, 550), f"Duration: {duration}", fill=(190, 190, 190), font=small_font)

        # 6. Progress Bar
        bar_x1, bar_x2, bar_y = 750, 1800, 840
        draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 14), radius=7, fill=(255, 255, 255, 50))
        draw.rounded_rectangle((bar_x1, bar_y, bar_x1 + 450, bar_y + 14), radius=7, fill=(0, 255, 255, 200))
        draw.text((bar_x1, bar_y + 35), "00:00", fill="white", font=small_font)
        draw.text((bar_x2 - 110, bar_y + 35), duration, fill="white", font=small_font)

        # 7. Large Footer Branding
        draw_text_with_glow(draw, (90, 940), "BETA BOT HUB", branding_font, (132, 224, 240), (0, 255, 255, 120))
        draw_text_with_glow(draw, (1480, 940), "👑 THE SHIV", branding_font, (255, 60, 160), (255, 0, 170, 120))

        # Cleanup & Save
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        
        if user_photo_path and os.path.exists(user_photo_path):
            try:
                os.remove(user_photo_path)
            except:
                pass
        
        background = background.convert("RGB")
        background.save(final_path, "PNG", quality=95)  # Changed to PNG
        return final_path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return YOUTUBE_IMG_URL
