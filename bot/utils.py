from models import Subscription
from spider import get_spider


async def subscription_telegram_message_text(subscription: Subscription) -> str:
    """
    生成Telegram消息
    """

    text = f"Sub: `{subscription.name}`{' - 已停止' if not subscription.enable else ''}\n"
    text += f"URL: {subscription.url}\n"
    text += f"Cron: `{subscription.cron}`\n"
    spider = get_spider(subscription)
    text += f"Spider: { spider.description + ' - ' + spider.name if spider else '无'}\n"
    text += f"Actions:\n"
    for action in subscription.actions:
        action_text = f"{action.description} - {action.name}\n"
        # 配置，先转换为dict，然后字 段: 值 打印
        action_text += f"Config:\n"
        action_text += await action.dynamic_config.telegram_text()
        text += action_text
        # 分隔符
        text += f"\n{'-'*10}\n"
    return text
