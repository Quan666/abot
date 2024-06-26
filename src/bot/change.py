from typing import Dict, List, Optional
from telethon import TelegramClient, events
from src.action import ACTIONS
from src.action.base import BaseAction, BaseActionDynamicConfig
from src.bot.inputs import (
    choose_actions,
    choose_spider,
    cron_input,
    subscription_name_input,
    url_input,
)
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
from src.database import load_subscriptions, update_subscription
from src.models import Subscription
from src.spider import get_spider_support_actions_by_name


async def change_filed(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    sub: Subscription,
):
    """
    修改字段
    """

    old_sub = sub.copy()
    while True:
        btns = [
            InputButton("名称", data="name"),
            InputButton("Cron", data="cron"),
            InputButton("Spider", data="spider"),
            InputButton("白名单关键词", data="white_keywords"),
            InputButton("黑名单关键词", data="black_keywords"),
            InputButton("Actions", data="actions"),
            (
                InputButton("停止", data="enable")
                if sub.enable
                else InputButton("启用", data="enable")
            ),
            (
                InputButton("不使用代理", data="enable_proxy")
                if sub.enable_proxy
                else InputButton("开启代理", data="enable_proxy")
            ),
            InputButtonCancel(),
            InputButtonConfirm(),
        ]
        try:
            btn = await InputBtns(
                bot,
                event,
                f"{await subscription_telegram_message_text(sub)}\n选择要修改的字段",
                btns,
            ).input()
        except CancelInput:
            return
        try:
            if btn == "name":
                sub.name = await subscription_name_input(bot, event, "名称")
            elif btn == "cron":
                sub.cron = await cron_input(bot, event, sub.cron)
            elif btn == "spider":
                sub.spider = await choose_spider(bot, event, "", sub.spider)
            elif btn == "actions":
                sub.actions = await choose_actions(
                    bot,
                    event,
                    "选择 Action",
                    support_actions=get_spider_support_actions_by_name(sub.spider.name),
                    actions_select=sub.actions,
                )
            elif btn == "enable":
                sub.enable = not sub.enable
            elif btn == "enable_proxy":
                sub.enable_proxy = not sub.enable_proxy
            elif btn == "white_keywords":
                sub.white_keywords = await InputListStr(
                    bot,
                    event,
                    "输入白名单关键词, 为空则不限制\n支持正则表达式, 满足其中一个关键词则推送",
                    sub.white_keywords,
                ).input()
            elif btn == "black_keywords":
                sub.black_keywords = await InputListStr(
                    bot,
                    event,
                    "输入黑名单关键词, 为空则不限制\n支持正则表达式, 满足其中一个关键词则不推送",
                    sub.black_keywords,
                ).input()

            elif btn == CONFIRM:
                await update_subscription(old_sub, sub)
                await event.reply(
                    f"修改成功\n{await subscription_telegram_message_text(sub)}",
                )
                return
        except CancelInput:
            continue


async def change_list(
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
        btn = await InputBtns(bot, event, "选择要修改的订阅", btns).input()
        if btn == CANCEL:
            return
        sub = next((sub for sub in subs if sub.name == btn), None)
        if sub:
            await change_filed(bot, event, sub)
