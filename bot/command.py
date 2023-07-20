import asyncio
from telethon import TelegramClient, events, sync, Button
from bot import bot
from bot.inputs import choose_actions, choose_spider, cron_input, subscription_name_input
from bot.lib import CancelInput, CommandInfo, InputText, buttons_layout
from bot.permission import handle_permission
from config import config
from database import add_subscription
from models import Subscription
from spider import get_spider_support_actions_by_name


class StratCommands:
    subscribe = CommandInfo(name="订阅", command="subscribe", description="订阅")
    change = CommandInfo(name="修改", command="change", description="修改订阅")
    query = CommandInfo(name="查询", command="query", description="查询订阅")
    unsubscribe = CommandInfo(name="取消订阅", command="unsubscribe", description="取消订阅")
    help = CommandInfo(name="帮助", command="help", description="帮助")


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
async def change(event: events.CallbackQuery.Event) -> None:
    await event.delete()
    try:

        sub_name = await subscription_name_input(bot, event, "订阅名称")
        sub_url = await InputText(bot, event, "订阅地址").input()
        sub_cron = await cron_input(bot, event)

        spider_name = await choose_spider(bot, event, "选择抓取方式", sub_url)

        # actions 选择
        actions = await choose_actions(
            bot, event, "选择 Action", get_spider_support_actions_by_name(spider_name)
        )
        sub = Subscription(
            name=sub_name,
            url=sub_url,
            cron=sub_cron,
            spider_name=spider_name,
            actions=actions,
            enable=True,
        )
        await add_subscription(sub)
        await event.reply("添加成功")

    except asyncio.TimeoutError:
        pass
    except CancelInput as e:
        pass
    except Exception as e:
        print(e)
