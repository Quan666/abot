
from telethon import TelegramClient, events, sync, Button
from bot import bot

@bot.on(events.NewMessage(pattern="/start"))
async def start(event: events.newmessage.NewMessage.Event):
    await event.message.reply("Hello World")