from typing import Dict, List, Optional
from telethon import TelegramClient, events
from src.action import ACTIONS
from src.action.base import BaseAction, BaseActionDynamicConfig
from src.bot.lib import (
    CANCEL,
    CONFIRM,
    CancelInput,
    InputBtns,
    InputBtnsBool,
    InputButton,
    InputButtonCancel,
    InputButtonConfirm,
    InputListStr,
    InputText,
)
from src.bot.utils import subscription_telegram_message_text
from src.database import load_subscriptions


async def query_list(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
):

    """
    查询列表
    """
    subs = await load_subscriptions()
    if not subs:
        await event.reply("没有订阅, 快去添加吧!")
        return
    btns = []
    for sub in subs:
        btn = InputButton(sub.name, data=sub.name)
        btns.append(btn)
    btns.append(InputButtonCancel())
    while True:
        btn = await InputBtns(bot, event, "选择要查看的订阅", btns).input()
        if btn == CANCEL:
            return
        sub = next((sub for sub in subs if sub.name == btn), None)
        if sub:
            await event.reply(
                await subscription_telegram_message_text(sub),
            )
