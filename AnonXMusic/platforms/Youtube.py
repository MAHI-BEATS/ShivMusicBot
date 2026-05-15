import asyncio
import glob
import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Union, Optional
import string
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ytSearch import VideosSearch, Playlist
from AnonXMusic import LOGGER
from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds
from config import YT_API_KEY, YTPROXY_URL as YTPROXY

logger = LOGGER(__name__)

def cookie_txt_file():
    try:
        folder_path = f"{os.getcwd()}/cookies"
        filename = f"{os.getcwd()}/cookies/logs.csv"
        txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
        if not txt_files:
            raise FileNotFoundError("No .txt files found in the specified folder.")
        cookie_txt_file = random.choice(txt_files)
        with open(filename, 'a') as file:
            file.write(f'Choosen File : {cookie_txt_file}\n')
        return f"""cookies/{str(cookie_txt_file).split("/")[-1]}"""
    except:
        return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\$[0-?]*[ -/]*[@-~])")
        self.dl_stats = {
            "total_requests": 0,
            "okflix_downloads": 0,
            "cookie_downloads": 0,
            "existing_files": 0
        }

    def _clean_link(self, link: str, videoid: Union[bool, str] = None) -> str:
        """Clean and normalize YouTube link"""
        if videoid:
            link = self.base + link
        
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        return link

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Optional[str]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        return text[offset : offset + length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        link = self._clean_link(link, videoid)
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = 0 if str(duration_min) == "None" else int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._clean_link(link, videoid)
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]
        return "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._clean_link(link, videoid)
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]
        return "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._clean_link(link, videoid)
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]
        return ""

    async def video(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        link = self._clean_link(link, videoid)
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        return 0, stderr.decode()

    async def playlist(self, link: str, limit: int, user_id: int, videoid: Union[bool, str] = None):
        link = self._clean_link(link, videoid)
        playlist = await Playlist.get(link)
        if not playlist:
            return None
        
        videos = []
        for video in playlist["videos"][:limit]:
            try:
                duration = video.get("duration", "0:00")
                duration_sec = int(time_to_seconds(duration)) if duration else 0
                videos.append({
                    "vidid": video["id"],
                    "title": video.get("title", "Unknown"),
                    "duration_min": duration,
                    "duration_sec": duration_sec,
                    "thumbnail": video.get("thumbnails", [{}])[0].get("url", "").split("?")[0] if video.get("thumbnails") else "",
                })
            except Exception:
                continue
        return videos

    async def track(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        link = self._clean_link(link, videoid)
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        link = self._clean_link(link, videoid)
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        
        with ydl:
            r = ydl.extract_info(link, download=False)
            formats_available = []
            for format_info in r["formats"]:
                try:
                    format_str = str(format_info["format"])
                    if "dash" in format_str.lower():
                        continue
                except:
                    continue
                
                try:
                    formats_available.append({
                        "format": format_info["format"],
                        "filesize": format_info.get("filesize"),
                        "format_id": format_info["format_id"],
                        "ext": format_info["ext"],
                        "format_note": format_info.get("format_note", ""),
                        "yturl": link,
                    })
                except KeyError:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None) -> tuple:
        link = self._clean_link(link, videoid)
        try:
            search = VideosSearch(link, limit=10)
            search_results = (await search.next()).get("result", [])
            results = []

            for result in search_results:
                duration_str = result.get("duration", "0:00")
                try:
                    parts = duration_str.split(":")
                    duration_secs = 0
                    if len(parts) == 3:
                        duration_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration_secs = int(parts[0]) * 60 + int(parts[1])
                    
                    if duration_secs <= 3600:  # 1 hour limit
                        results.append(result)
                except (ValueError, IndexError):
                    continue

            if not results or query_type >= len(results):
                raise ValueError("No suitable videos found within duration limit")

            selected = results[query_type]
            return (
                selected["title"],
                selected["duration"],
                selected["thumbnails"][0]["url"].split("?")[0],
                selected["id"]
            )
        except Exception as e:
            logger.error(f"Error in slider: {str(e)}")
            raise ValueError("Failed to fetch video details")

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> tuple:
        if videoid:
            vid_id = link
            link = self.base + link
        
        # Ensure downloads directory exists
        os.makedirs("downloads", exist_ok=True)
        
        loop = asyncio.get_running_loop()

        def create_session():
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.1)
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))
            return session

        async def download_with_requests(url: str, filepath: str, headers: dict = None) -> Optional[str]:
            try:
                session = create_session()
                response = session.get(
                    url, headers=headers, stream=True, timeout=60, allow_redirects=True
                )
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                
                session.close()
                return filepath
                
            except Exception as e:
                logger.error(f"Requests download failed: {str(e)}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None

        async def api_download(vid_id: str, file_ext: str, api_type: str = "audio") -> Optional[str]:
            try:
                if not YT_API_KEY:
                    logger.error("API KEY not set in config")
                    return None
                if not YTPROXY:
                    logger.error("API Endpoint not set in config")
                    return None
                
                headers = {
                    "x-api-key": YT_API_KEY,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                filepath = os.path.join("downloads", f"{vid_id}.{file_ext}")
                if os.path.exists(filepath):
                    self.dl_stats["existing_files"] += 1
                    return filepath
                
                session = create_session()
                api_url = f"{YTPROXY}/info/{vid_id}"
                response = session.get(api_url, headers=headers, timeout=60)
                
                try:
                    data = response.json()
                except Exception as e:
                    logger.error(f"Invalid response from API: {str(e)}")
                    return None
                finally:
                    session.close()
                
                status = data.get('status')
                if status == 'success':
                    download_url = data.get(f"{api_type}_url")
                    if download_url:
                        result = await download_with_requests(download_url, filepath, headers)
                        if result:
                            self.dl_stats[api_type + "_downloads"] += 1
                            return result
                elif status == 'error':
                    logger.error(f"API Error: {data.get('message', 'Unknown error')}")
                
                return None
                
            except Exception as e:
                logger.error(f"Error in {api_type} download: {str(e)}")
                return None

        # Main download logic
        if songvideo:
            return await api_download(vid_id, "mp4", "video"), True
        elif songaudio:
            return await api_download(vid_id, "mp3", "audio"), True
        elif video:
            return await api_download(vid_id, "mp4", "video"), True
        else:
            return await api_download(vid_id, "mp3", "audio"), True
