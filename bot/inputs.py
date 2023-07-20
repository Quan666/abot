from typing import Dict, List, Optional
from telethon import  TelegramClient, events
from action import ACTIONS
from action.base import BaseAction, BaseActionDynamicConfig
from bot.lib import (
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
from spider import match_spider
from subscription import load_subscription
from utils import create_trigger


async def subscription_name_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str)-> Optional[str]:
    """
    订阅名称输入
    """
    while True:
        name = await InputText(bot, event, tips_text).input()
        sub_names = [sub.name for sub in await load_subscription()]
        if name in sub_names:
            tips_text = f"{tips_text}\n订阅名称已存在, 请重新输入!!!"
        else:
            return name
    
async def cron_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
) -> str:
    """
    cron 表达式输入
    """
    sub_cron = None
    placeholder = "0 */5 * * * *"
    tips_text = f"订阅更新 Cron 表达式\n如: `{placeholder}`\n表示每5分钟更新一次"
    while True:
        if sub_cron is None:
            sub_cron = await InputText(bot, event, tips_text).input(
                placeholder=placeholder
            )
        else:
            sub_cron = await InputText(bot, event, f"Cron 表达式错误, 请重新输入!!!\n{tips_text}").input(
                placeholder=placeholder
            )
        if create_trigger(sub_cron):
            break
    return sub_cron


async def action_config_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    action_name: str,
    action: BaseAction,
) -> BaseActionDynamicConfig:
    """
    根据 action 的 config 类含有哪些字段、以及字段类型判断输入方式
    """
    config = action.dynamic_config
    await config.telegram_setting(bot=bot, event=event)
    return config



async def choose_actions(
    bot: TelegramClient, event: events.CallbackQuery.Event, tips_text: str, support_actions: List[str]
) -> List[BaseAction]:
    """
    选择 actions,多选
    """
    btns = []
    actions_select = []
    actions: Dict[str,BaseAction] = {}
    for action_name, action_cls in ACTIONS.items():
        if action_name not in support_actions:
            continue
        action = action_cls()
        actions[action_name] = action
        btns.append(InputButton(action.description, action_name))

    # 取消按钮
    btns.append(InputButtonCancel())
    # 确认按钮
    btns.append(InputButtonConfirm())

    actions_name: List[str] = []

    while True:
        result = await InputBtns(
            bot, event, f"{tips_text}\n已选择:\n{', '.join(actions_name)}", btns
        ).input()
        # 如果取消
        if CONFIRM == result:
            break
        if result and result not in actions_select:
            config = await action_config_input(bot, event, result, actions[result])
            actions[result].dynamic_config = config
            actions_select.append(actions[result])
            actions_name.append(actions[result].description)

    return actions_select


async def choose_spider(
    bot: TelegramClient, event: events.CallbackQuery.Event, tips_text: str, url: str
) -> str:
    """
    选择 Spider, 单选
    """
    btns = []
    spiders = match_spider(url)

    for spider in spiders:
        btns.append(InputButton(spider.description, spider.name))

    # 取消按钮
    btns.append(InputButtonCancel())

    return await InputBtns(
        bot, event, f"{tips_text}\nURL: {url}\n匹配到的抓取方式有:", btns
    ).input()
