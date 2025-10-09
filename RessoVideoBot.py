import os
import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputStream, InputAudioStream, InputVideoStream
import yt_dlp
from dotenv import load_dotenv

# --------------------------
# Load environment variables
# --------------------------
load_dotenv()
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

# --------------------------
# Folder setup
# --------------------------
DOWNLOADS = Path("./downloads")
DOWNLOADS.mkdir(exist_ok=True)

# --------------------------
# Pyrogram clients
# --------------------------
bot = Client("RessoVideoBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("RessoAssistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) if SESSION_STRING else None

# --------------------------
# PyTgCalls initialization
# --------------------------
calls_client = None

# --------------------------
# Queue system
# --------------------------
class Track:
    def __init__(self, title: str, file_path: Path, requested_by: str, is_video: bool = False):
        self.title = title
        self.file_path = file_path
        self.requested_by = requested_by
        self.is_video = is_video

queues: Dict[int, List[Track]] = {}
playing: Dict[int, Track] = {}

# --------------------------
# YT-DLP Options
# --------------------------
YTDL_OPTS_AUDIO = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': '%(id)s.%(ext)s',
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
}

YTDL_OPTS_VIDEO = {
    'format': 'bestvideo+bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': '%(id)s.%(ext)s',
}

# --------------------------
# Utility functions
# --------------------------
async def ensure_calls_client():
    global calls_client
    if calls_client:
        return
    client_for_calls = user if user else bot
    calls_client = PyTgCalls(client_for_calls)
    await calls_client.start()

async def download_media(query: str) -> Tuple[Path, str, bool]:
    temp_dir = tempfile.mkdtemp(prefix="resso_")
    is_video = False
    opts = YTDL_OPTS_AUDIO if not query.endswith(('.mp4','.mkv','.webm')) else YTDL_OPTS_VIDEO
    with yt_dlp.YoutubeDL(opts) as ydl:
        to_fetch = query if query.startswith(('http://','https://')) else f"ytsearch1:{query}"
        info = ydl.extract_info(to_fetch, download=True)
        if 'entries' in info:
            info = info['entries'][0]

        filename = None
        for root, _, files in os.walk(temp_dir):
            for f in files:
                if f.lower().endswith(('.mp3','.m4a','.opus')):
                    filename = os.path.join(root,f)
                    break
                if f.lower().endswith(('.mp4','.mkv','.webm')):
                    filename = os.path.join(root,f)
                    is_video = True
                    break
            if filename:
                break

        if not filename:
            raise Exception("Failed to find downloaded file")

        dest = DOWNLOADS / Path(filename).name
        shutil.move(filename, dest)
        shutil.rmtree(temp_dir, ignore_errors=True)
        title = info.get('title','Unknown title')
        return dest, title, is_video

async def start_playback(chat_id: int):
    await ensure_calls_client()
    q = queues.get(chat_id, [])
    if not q:
        return
    track = q.pop(0)
    playing[chat_id] = track
    try:
        stream = InputAudioStream(str(track.file_path))
        if track.is_video:
            stream = InputStream(InputAudioStream(str(track.file_path)),
                                 InputVideoStream(str(track.file_path)))
        await calls_client.join_group_call(chat_id, stream)
    except Exception as e:
        q.insert(0, track)
        raise e

async def play_next(chat_id: int):
    try:
        await calls_client.leave_group_call(chat_id)
    except Exception:
        pass
    playing.pop(chat_id,None)
    if queues.get(chat_id):
        await start_playback(chat_id)

# --------------------------
# Stream end handler
# --------------------------
@PyTgCalls.on_stream_end
async def _on_stream_end_handler(update: Update):
    chat_id = update.chat_id
    asyncio.create_task(play_next(chat_id))

# --------------------------
# Bot commands
# --------------------------
@bot.on_message(filters.command("start"))
async def start_cmd(_, message: Message):
    await message.reply_text("🎵 Resso Video Bot Ready!\nUse /playvideo <url or query> in a group to play music/video.")

@bot.on_message(filters.command("help"))
async def help_cmd(_, message: Message):
    await message.reply_text(
        "Commands:\n"
        "/playvideo <query or URL> - Play audio/video\n"
        "/pause - Pause playback\n"
        "/resume - Resume playback\n"
        "/skip - Skip current\n"
        "/stop - Stop playback"
    )

@bot.on_message(filters.command("playvideo"))
async def playvideo_cmd(_, message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        await message.reply_text("❌ This command works in groups only!")
        return
    if len(message.command)<2:
        await message.reply_text("Usage: `/playvideo <search query or URL>`")
        return
    query = " ".join(message.command[1:])
    msg = await message.reply_text(f"🔎 Searching for: {query}")
    try:
        file_path, title, is_video = await download_media(query)
    except Exception as e:
        await msg.edit(f"❌ Failed: {e}")
        return
    track = Track(title, file_path, message.from_user.first_name, is_video)
    queues.setdefault(chat_id,[]).append(track)
    await msg.edit(f"✅ Added to queue: {title}\n🎧 Position: {len(queues[chat_id])}")
    if chat_id not in playing:
        try:
            await start_playback(chat_id)
            await message.reply_text(f"▶️ Now playing: {title}")
        except Exception as e:
            await message.reply_text(f"❌ Could not start playback: {e}")

@bot.on_message(filters.command("pause"))
async def pause_cmd(_, message: Message):
    try:
        await calls_client.pause_stream(message.chat.id)
        await message.reply_text("⏸️ Paused")
    except Exception as e:
        await message.reply_text(f"❌ Pause failed: {e}")

@bot.on_message(filters.command("resume"))
async def resume_cmd(_, message: Message):
    try:
        await calls_client.resume_stream(message.chat.id)
        await message.reply_text("▶️ Resumed")
    except Exception as e:
        await message.reply_text(f"❌ Resume failed: {e}")

@bot.on_message(filters.command("skip"))
async def skip_cmd(_, message: Message):
    try:
        await calls_client.leave_group_call(message.chat.id)
        await message.reply_text("⏭️ Skipped")
        if queues.get(message.chat.id):
            await start_playback(message.chat.id)
    except Exception as e:
        await message.reply_text(f"❌ Skip failed: {e}")

@bot.on_message(filters.command("stop"))
async def stop_cmd(_, message: Message):
    try:
        await calls_client.leave_group_call(message.chat.id)
    except Exception:
        pass
    queues.pop(message.chat.id,None)
    playing.pop(message.chat.id,None)
    await message.reply_text("⏹️ Stopped and cleared queue")

# --------------------------
# Run bot
# --------------------------
async def main():
    await bot.start()
    if user:
        await user.start()
    await ensure_calls_client()
    print("🎧 Resso Video Bot started. Press Ctrl+C to stop.")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())