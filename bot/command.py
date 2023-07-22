import asyncio
from loguru import logger
from telethon import TelegramClient, events, sync, Button
from bot import bot
from bot.change import change_list
from bot.delete import delete_handle
from bot.inputs import (
    choose_actions,
    choose_spider,
    cron_input,
    subscription_name_input,
    url_input,
)
from bot.lib import CancelInput, CommandInfo, InputText, buttons_layout
from bot.permission import handle_permission
from bot.query import query_list
from bot.utils import subscription_telegram_message_text
from config import config
from database import add_subscription, load_subscriptions
from models import Subscription
from spider import get_spider_support_actions_by_name


class StratCommands:
    subscribe = CommandInfo(name="订阅", command="subscribe", description="订阅")
    change = CommandInfo(name="修改", command="change", description="修改订阅")
    query = CommandInfo(name="查询", command="query", description="查询订阅")
    unsubscribe = CommandInfo(name="删除订阅", command="unsubscribe", description="删除订阅")


@bot.on(events.NewMessage(pattern="/info", from_users=config.telegram_admin_ids))  # type: ignore
async def start(event: events.NewMessage.Event) -> None:
    """
    输出当前对话的相关信息
    """
    text = f"chat_id: `{event.chat_id}`\n"
    text += f"sender_id: `{event.sender_id}`\n"
    await event.reply(text)


@bot.on(events.NewMessage(pattern="/start", from_users=config.telegram_admin_ids))  # type: ignore
async def start(event: events.NewMessage.Event) -> None:
    btns = []
    for command in StratCommands.__dict__.values():
        if isinstance(command, CommandInfo):
            btn = Button.inline(command.name, data=command.command)
            btns.append(btn)
    await event.reply(
        "选择操作:",
        buttons=buttons_layout(btns),
    )


@bot.on(events.CallbackQuery(data=StratCommands.subscribe.command, func=lambda e: handle_permission(e)))  # type: ignore
async def subscribe(event: events.CallbackQuery.Event) -> None:
    await event.delete()
    try:
        sub_names = [sub.name for sub in await load_subscriptions()]
        sub_name = await subscription_name_input(bot, event, "名称", sub_names)
        sub_cron = await cron_input(bot, event)

        spider = await choose_spider(bot, event, "选择 Spider")

        # actions 选择
        actions = await choose_actions(
            bot, event, "选择 Action", get_spider_support_actions_by_name(spider.name)
        )
        sub = Subscription(
            name=sub_name,
            cron=sub_cron,
            spider=spider,
            actions=actions,
            enable=True,
        )
        await add_subscription(sub)
        await event.reply(f"添加成功\n{await subscription_telegram_message_text(sub)}")

    except asyncio.TimeoutError:
        pass
    except CancelInput as e:
        pass
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error(e)


@bot.on(events.CallbackQuery(data=StratCommands.change.command, func=lambda e: handle_permission(e)))  # type: ignore
async def change(event: events.CallbackQuery.Event) -> None:
    """
    修改订阅
    """
    await event.delete()
    try:
        await change_list(bot, event)
    except asyncio.TimeoutError:
        pass
    except CancelInput:
        pass


@bot.on(events.CallbackQuery(data=StratCommands.query.command, func=lambda e: handle_permission(e)))  # type: ignore
async def query(event: events.CallbackQuery.Event) -> None:
    """
    查询订阅
    """
    await event.delete()
    try:
        await query_list(bot, event)
    except asyncio.TimeoutError:
        pass
    except CancelInput:
        pass


@bot.on(events.CallbackQuery(data=StratCommands.unsubscribe.command, func=lambda e: handle_permission(e)))  # type: ignore
async def unsubscribe(event: events.CallbackQuery.Event) -> None:
    """
    删除订阅
    """
    await event.delete()
    try:
        await delete_handle(bot, event)
    except asyncio.TimeoutError:
        pass
    except CancelInput:
        pass
