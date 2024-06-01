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
from src.database import delete_subscription, load_subscriptions


async def delete_handle(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
):
    """
    删除订阅
    """
    delete_fisrt = True
    while True:
        subs = await load_subscriptions()
        if not subs:
            if delete_fisrt:
                await event.reply("没有订阅!")
            return
        btns = []
        for sub in subs:
            btn = InputButton(sub.name, data=sub.name)
            btns.append(btn)
        btns.append(InputButtonCancel())
        btn = await InputBtns(bot, event, "选择要删除的订阅", btns).input()
        if btn == CANCEL:
            return
        sub = next((sub for sub in subs if sub.name == btn), None)
        if sub:
            # 确认删除
            try:
                e = await InputBtns(
                    bot,
                    event,
                    f"确认删除 {sub.name} 订阅?\n{await subscription_telegram_message_text(sub)}",
                    [InputButtonConfirm(), InputButtonCancel()],
                ).input()
                if e == CONFIRM:
                    await delete_subscription(sub)
                    await event.reply(
                        f"删除 {sub.name} 订阅成功!\n{await subscription_telegram_message_text(sub)}"
                    )
                    delete_fisrt = False
            except CancelInput:
                continue
