import re
from typing import Any, Dict, List, Optional
from telethon import TelegramClient, events
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
from spider import get_all_spider
from utils import create_trigger


async def subscription_name_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str,
    sub_names: List[str] = [],
) -> Optional[str]:
    """
    订阅名称输入
    """
    while True:
        name = await InputText(bot, event, tips_text).input()
        if name in sub_names:
            tips_text = f"{tips_text}\n订阅名称已存在, 请重新输入!!!"
        else:
            return name


async def url_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str,
    placeholder: str = "https://",
) -> Optional[str]:
    """
    url 输入, 正则匹配是否为 url
    """
    rex = re.compile(r"^((http|https)?:\/\/)[^\s]+")

    while True:
        url = await InputText(bot, event, tips_text).input(placeholder)
        if url and rex.match(url):
            return url
        else:
            tips_text = f"{tips_text}\nURL 错误, 请重新输入!!!"


async def cron_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    cron: Optional[str] = None,
) -> str:
    """
    cron 表达式输入
    """
    sub_cron = None
    if not cron:
        placeholder = "0 */5 * * * *"
        tips_text = f"订阅执行 Cron 表达式\n如: `{placeholder}`\n表示每5分钟执行一次"
    else:
        placeholder = cron
        tips_text = f"订阅执行 Cron 表达式\n当前: `{cron}`"
    while True:
        if sub_cron is None:
            sub_cron = await InputText(bot, event, tips_text).input(
                placeholder=placeholder
            )
        else:
            sub_cron = await InputText(
                bot, event, f"Cron 表达式错误, 请重新输入!!!\n{tips_text}"
            ).input(placeholder=placeholder)
        if create_trigger(sub_cron):
            break
    return sub_cron


async def action_config_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    action: BaseAction,
) -> BaseActionDynamicConfig:
    """
    根据 action 的 config 类含有哪些字段、以及字段类型判断输入方式
    """
    config = action.dynamic_config
    await config.telegram_setting(bot=bot, event=event)
    return config


async def choose_actions_delete(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str,
    actions_select: List[BaseAction] = [],
) -> List[BaseAction]:
    """
    删除 actions, 点击按钮删除
    """
    btns = []
    old_actions_select = actions_select.copy()
    for action in actions_select:
        btns.append(InputButton(action.description, action.name))

    # 取消按钮
    btns.append(InputButtonCancel())
    # 确认按钮
    btns.append(InputButtonConfirm())

    actions_name: List[str] = [action.description for action in actions_select]

    while True:
        try:
            result = await InputBtns(
                bot,
                event,
                f"{tips_text}\n已选择:\n{', '.join(actions_name)}\n点击按钮删除",
                btns,
            ).input()
            if CONFIRM == result:
                break
            if result and result:
                # 如果选择了
                for action in actions_select:
                    if action.name == result:
                        actions_select.remove(action)
                        actions_name.remove(action.description)
        except CancelInput:
            return old_actions_select
    return actions_select


async def choose_actions(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str,
    support_actions: List[str],
    actions_select: List[BaseAction] = [],
) -> List[BaseAction]:
    """
    选择 actions,多选
    """
    btns = []
    actions: Dict[str, BaseAction] = {}
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
    # 删除按钮
    btns.append(InputButton("删除", data="delete"))

    actions_name: List[str] = [action.description for action in actions_select]

    while True:
        result = await InputBtns(
            bot, event, f"{tips_text}\n已选择:\n{', '.join(actions_name)}", btns
        ).input()
        if CONFIRM == result:
            break
        if "delete" == result:
            actions_select = await choose_actions_delete(
                bot, event, "删除 Action", actions_select=actions_select
            )
            actions_name = [action.description for action in actions_select]

        elif result:
            # 如果选择了
            action_ = actions[result]
            exist = False
            for action in actions_select:
                if action.name == action_.name:
                    action_ = action
                    exist = True

            config = await action_config_input(bot, event, action_)
            action_.dynamic_config = config
            if not exist:
                actions_select.append(actions[result])
                actions_name.append(actions[result].description)

    return actions_select


async def spider_config_input(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    spider,
) -> Any:
    """
    根据 spider 的 config 类含有哪些字段、以及字段类型判断输入方式
    """
    config = spider.dynamic_config
    await config.telegram_setting(bot=bot, event=event)
    return config


async def choose_spider(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str,
    old_spider=None,
) -> Any:
    """
    选择 Spider, 单选
    """
    btns = []
    spiders = get_all_spider()
    text = ""
    if old_spider:
        btns.append(InputButton(old_spider.description, old_spider.name))
        text = f"当前 Spider: {old_spider.description}\n可以点击对应方式修改配置或切换其它方式"
    for spider in spiders:
        if old_spider and spider.name == old_spider.name:
            continue
        btns.append(InputButton(spider.description, spider.name))

    # 取消按钮
    btns.append(InputButtonCancel())

    while True:
        select = await InputBtns(bot, event, f"{tips_text}\n{text}", btns).input()
        if select:
            for spider in spiders:
                if spider.name == select:
                    spider_ = spider
                    if old_spider and spider.name == old_spider.name:
                        spider_ = old_spider
                    config = await spider_config_input(bot, event, spider_)
                    spider_.dynamic_config = config
                    return spider_
