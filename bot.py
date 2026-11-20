import sys
import glob
import importlib
from pathlib import Path
from pyrogram import Client, idle, __version__
from pyrogram.raw.all import layer
import time
import asyncio
from datetime import date, datetime
import pytz
from aiohttp import web
from database.ia_filterdb import Media, Media2
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from plugins import web_server, check_expired_premium 
from Lucia.Bot import SilentX
from Lucia.util.keepalive import ping_server
from Lucia.Bot.clients import initialize_clients
import pyrogram.utils
from PIL import Image
import threading, time, requests
from logging_helper import LOGGER
from shared.database.indexes import ensure_all_indexes
from workers.scheduler import background_worker

botStartTime = time.time()
ppath = "plugins/*.py"
files = glob.glob(ppath)

pyrogram.utils.MIN_CHANNEL_ID = -1002719012453

def ping_loop():
    if not (URL and URL.startswith("http") and not "localhost" in URL):
        return
    while True:
        try:
            r = requests.get(URL, timeout=10)
            if r.status_code == 200:
                LOGGER.info("✅ Keep-alive Ping Successful")
        except Exception:
            pass
        time.sleep(180)

if ON_HEROKU:
    threading.Thread(target=ping_loop, daemon=True).start()

async def SilentXBotz_start():
    LOGGER.info('Initalizing Your Bot!')
    await SilentX.start()
    bot_info = await SilentX.get_me()
    SilentX.username = bot_info.username
    await initialize_clients()
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            LOGGER.info("Import Plugins - " + plugin_name)
    if ON_HEROKU:
        asyncio.create_task(ping_server()) 
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    await Media.ensure_indexes()
    await ensure_all_indexes()
    background_worker.start(SilentX)
    if MULTIPLE_DB:
        await Media2.ensure_indexes()
        LOGGER.info("Multiple Database Mode On. Now Files Will Be Save In Second DB If First DB Is Full")
    else:
        LOGGER.info("Single DB Mode On ! Files Will Be Save In First Database")
    me = await SilentX.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    temp.B_LINK = me.mention
    SilentX.username = '@' + me.username
    SilentX.loop.create_task(check_expired_premium(SilentX))
    LOGGER.info(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    LOGGER.info(script.LOGO)
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    try:
        if LOG_CHANNEL:
            await SilentX.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(temp.B_LINK, today, time))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        LOGGER.warning(f"Failed to send restart message to LOG_CHANNEL: {e}")

    for admin in ADMINS:
        try:
            await SilentX.send_message(chat_id=admin, text=f"<b>๏[-ิ_•ิ]๏ {me.mention} Restarted ✅</code></b>")
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    site = web.TCPSite(app, bind_address, PORT)
    await site.start()
    LOGGER.info(f"Web server started on {bind_address}:{PORT}")

    try:
        await idle()
    finally:
        LOGGER.info("Initiating graceful shutdown...")
        try:
            background_worker.stop()
        except Exception:
            pass
        try:
            await app.cleanup()
        except Exception:
            pass
        try:
            await SilentX.stop()
        except Exception:
            pass
        LOGGER.info("✅ Graceful shutdown completed.")
    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(SilentXBotz_start())
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info('Service Stopped Gracefully Bye 👋')
