from models import Subscription


async def subscription_telegram_message_text(subscription: Subscription) -> str:
    """
    生成Telegram消息
    """

    text = (
        f"Sub: `{subscription.name}`{' - *已停止*' if not subscription.enable else ''}\n"
    )
    text += f"Cron: `{subscription.cron}`\n"
    text += f"Proxy: {'开启' if subscription.enable_proxy else '关闭'}\n"
    text += (
        f"Spider: { subscription.spider.description if subscription.spider else '无'}\n"
    )
    text += f"{await subscription.spider.dynamic_config.telegram_text()}\n\n"
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
