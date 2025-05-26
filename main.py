import os
import io
import time
import aiohttp
import requests
from typing import Optional
from bs4 import BeautifulSoup
from telegram import (
    Update,
    InputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "8113755100:AAGcwpJzyWCuxwt-OT0RJsF1ZgcaumkZO6c"
SCREENSHOT_API = "https://image.thum.io/get/png/fullpage/viewportWidth/2400/"
TIKTOK_API = "https://api.tiklydown.eu.org/api/download"

class hencet_goreng:
    def __init__(self):
        self.start_time = time.time()
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CallbackQueryHandler(self.handle_button_click))
        self.app.add_handler(CommandHandler("ssweb", self.screenshot))
        self.app.add_handler(CommandHandler("remini", self.remini))
        self.app.add_handler(CommandHandler("tiktok", self.tiktok_downloader))
        self.app.add_handler(CommandHandler("runtime", self.runtime_command))
        self.app.add_handler(CommandHandler("play", self.play_music))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Runtime", callback_data="runtime")],
            [InlineKeyboardButton("Play Music", callback_data="play")],
            [InlineKeyboardButton("Screenshot Web", callback_data="ssweb")],
            [InlineKeyboardButton("Remini", callback_data="remini")],
            [InlineKeyboardButton("TikTok Downloader", callback_data="tiktok")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Pilih menu:", reply_markup=reply_markup)

    async def handle_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        command = query.data
        if command == "runtime":
            await self.runtime_command(update, context)
        elif command == "play":
            await query.edit_message_text("Masukkan judul lagu dengan perintah:\n`/play [judul lagu]`", parse_mode="Markdown")
        elif command == "ssweb":
            await query.edit_message_text("Masukkan URL dengan perintah:\n`/ssweb https://contoh.com`", parse_mode="Markdown")
        elif command == "remini":
            await query.edit_message_text("Balas gambar dan ketik:\n`/remini`", parse_mode="Markdown")
        elif command == "tiktok":
            await query.edit_message_text("Masukkan URL TikTok dengan perintah:\n`/tiktok https://vm.tiktok.com/...`", parse_mode="Markdown")

    async def screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text('Berikan URL web\nContoh: /ssweb https://www.nasa.gov')
            return
        url = context.args[0]
        try:
            screenshot_url = f"{SCREENSHOT_API}{url}"
            async with aiohttp.ClientSession() as session:
                async with session.get(screenshot_url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        await update.message.reply_photo(
                            photo=InputFile(io.BytesIO(image_data), filename="screenshot.png")
                        )
                    else:
                        await update.message.reply_text('Gagal mengambil screenshot')
        except Exception as e:
            await update.message.reply_text(f'Error: {str(e)}')

    async def remini(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message or not update.message.reply_to_message.photo:
            await update.message.reply_text('Balas gambar dengan caption /remini')
            return

        await update.message.reply_chat_action('upload_photo')
        try:
            photo = update.message.reply_to_message.photo[-1]
            file = await photo.get_file()
            image_data = await file.download_as_bytearray()
            enhanced_image = await self.enhance_image(image_data)
            if enhanced_image:
                await update.message.reply_photo(
                    photo=InputFile(io.BytesIO(enhanced_image), filename="enhanced.jpg"),
                    caption="Hasil peningkatan kualitas gambar"
                )
            else:
                await update.message.reply_text('Gagal meningkatkan kualitas gambar')
        except Exception as e:
            await update.message.reply_text(f'Error: {str(e)}')

    async def enhance_image(self, image_data: bytes) -> Optional[bytes]:
        try:
            url = "https://inferenceengine.vyro.ai/enhance"
            headers = {
                "User-Agent": "okhttp/4.9.3",
                "Connection": "Keep-Alive",
            }
            form_data = aiohttp.FormData()
            form_data.add_field("model_version", "1")
            form_data.add_field(
                "image", 
                image_data,
                filename="image.jpg",
                content_type="image/jpeg"
            )
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, data=form_data) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    return None
        except Exception:
            return None

    async def tiktok_downloader(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text('Berikan URL TikTok\nContoh: /tiktok https://vm.tiktok.com/xyz')
            return
        url = context.args[0]
        await update.message.reply_chat_action('upload_video')
        try:
            api_url = f"{TIKTOK_API}?url={requests.utils.quote(url)}"
            response = requests.get(api_url)
            data = response.json()
            if data.get('video', {}).get('noWatermark'):
                video_url = data['video']['noWatermark']
                caption = self._format_tiktok_caption(data)
                await update.message.reply_video(
                    video=video_url,
                    caption=caption,
                    parse_mode="Markdown"
                )
            else:
                video_data = await self._alternative_tiktok_download(url)
                if video_data:
                    await update.message.reply_video(
                        video=video_data['url'],
                        caption=f"Judul: {video_data.get('title', 'Tidak diketahui')}"
                    )
                else:
                    await update.message.reply_text('Gagal mendownload video TikTok')
        except Exception as e:
            await update.message.reply_text(f'Error: {str(e)}')

    def _format_tiktok_caption(self, data: dict) -> str:
        return f"""*TIKTOK DOWNLOADER*
*Dari*: {data.get('author', {}).get('name', 'Tidak diketahui')} (@{data.get('author', {}).get('unique_id', 'Tidak diketahui')})
*Like*: {data.get('stats', {}).get('likeCount', 'Tidak diketahui')}
*Komentar*: {data.get('stats', {}).get('commentCount', 'Tidak diketahui')}
*Share*: {data.get('stats', {}).get('shareCount', 'Tidak diketahui')}
*Putaran*: {data.get('stats', {}).get('playCount', 'Tidak diketahui')}
*Judul*: {data.get('title', 'Tidak diketahui')}"""

    async def _alternative_tiktok_download(self, url: str) -> Optional[dict]:
        try:
            return {
                'url': url.replace('tiktok.com', 'tikcdn.net') + '/video.mp4',
                'title': 'Video TikTok'
            }
        except Exception:
            return None

    def format_runtime(self, seconds):
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours} jam, {minutes} menit, {seconds} detik"

    async def runtime_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uptime = time.time() - self.start_time
        formatted = self.format_runtime(uptime)
        if update.callback_query:
            await update.callback_query.edit_message_text(f"*Bot telah online selama:*\n*{formatted}*", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"*Bot telah online selama:*\n*{formatted}*", parse_mode="Markdown")

    async def play_music(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text('Masukkan judul lagu!\nContoh: /play Jakarta Hari Ini')
            return

        query = " ".join(context.args)
        await update.message.reply_text("Tunggu sebentar, mencari lagu...")

        try:
            async with aiohttp.ClientSession() as session:
                api_url = f"https://api.nekorinn.my.id/downloader/spotifyplay?q={requests.utils.quote(query)}"
                async with session.get(api_url) as resp:
                    if resp.status != 200:
                        await update.message.reply_text('Gagal mengambil data lagu.')
                        return
                    data = await resp.json()
                    if not data.get("status"):
                        await update.message.reply_text('Lagu tidak ditemukan!')
                        return

                    metadata = data["result"]["metadata"]
                    download_url = data["result"]["downloadUrl"]

                    await update.message.reply_audio(
                        audio=download_url,
                        filename=f"{metadata.get('title', 'audio')}.mp3",
                        title=metadata.get("title"),
                        performer=metadata.get("artist"),
                        caption=f"*{metadata.get('title')}*\n{metadata.get('artist')} • {metadata.get('duration')}",
                        parse_mode="Markdown"
                    )
        except Exception as e:
            await update.message.reply_text(f'Error: {str(e)}')

    def run(self):
        print("Bot is running...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = hencet_goreng()
    bot.run()