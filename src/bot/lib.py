import asyncio
from typing import Any, List, Optional, Union

from telethon import Button, TelegramClient, events
from telethon.tl.types import Message, KeyboardButtonCallback


BUTTON_ROW_MAX_LEN = 40


class CancelInput(Exception):
    """
    取消输入
    """


class InputButton:
    def __init__(self, text: str, data: str):
        self.text = text
        self.data = data


CANCEL = "cancel"
CONFIRM = "confirm"


class InputButtonCancel(InputButton):
    def __init__(self):
        super().__init__("取消", "cancel")


class InputButtonConfirm(InputButton):
    def __init__(self):
        super().__init__("确认", "confirm")


async def wait_msg_callback(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    msg: str,
    timeout: float = 60,
    placeholder: Optional[str] = None,
    remove_text: bool = False,
) -> Message:
    # 等待用户发送消息
    # 需要用户输入的信息
    async with bot.conversation(
        await event.get_chat(), timeout=timeout, exclusive=False
    ) as conv:
        # @用户
        if event.sender.username:
            msg += f" \n@{event.sender.username}"
        else:
            # 文字提及用户
            msg += f" [@{event.sender.first_name}](tg://user?id={event.sender_id})"

        ans = await conv.send_message(
            msg,
            buttons=Button.force_reply(
                single_use=True,
                selective=True,
                placeholder=placeholder,
            ),
        )
        cancel_btn = await conv.send_message(
            "取消输入", buttons=[Button.inline("取消", "cancel")]
        )
        try:
            while True:
                # wait_event = [
                #     conv.get_response(timeout=timeout),
                #     conv.wait_event(
                #         events.CallbackQuery(
                #             func=lambda e: e.sender_id == event.sender_id
                #         ),
                #         timeout=timeout,
                #     ),
                # ]
                wait_event = [
                    asyncio.create_task(conv.get_response(timeout=timeout)),
                    asyncio.create_task(
                        conv.wait_event(
                            events.CallbackQuery(
                                func=lambda e: e.sender_id == event.sender_id
                            ),
                            timeout=timeout,
                        )
                    ),
                ]

                done, pending = await asyncio.wait(
                    wait_event, return_when=asyncio.FIRST_COMPLETED, timeout=timeout
                )
                try:
                    for task in pending:
                        task.cancel()
                    e = done.pop().result()
                except Exception as e:
                    raise asyncio.TimeoutError
                if (
                    isinstance(e, events.CallbackQuery.Event)
                    and e.data.decode() == CANCEL
                ):
                    await e.delete()
                    await cancel_btn.delete()
                    await ans.delete()
                    raise CancelInput
                if e.sender_id == event.sender_id:
                    return e

        finally:
            await cancel_btn.delete()
            if remove_text:
                await ans.delete()


def buttons_layout(btns: List[InputButton], size: int = 3) -> List[List[Button]]:
    """
    按钮布局，根据文字长度自动调整每行按钮数量
    一行最多 size 个按钮

    :param btns: 按钮列表
    :param size: 一行最多按钮数量
    """

    def _get_btn_len(btn: InputButton) -> int:
        """非 ASCII 算两个字符"""
        n = 0
        for c in btn.text:
            if ord(c) > 127:
                n += 2
            else:
                n += 1
        return n

    buttons_len = [_get_btn_len(btn) for btn in btns]
    result: List[List[Button]] = []
    row: List[KeyboardButtonCallback] = []
    row_len = 0
    for i, btn in enumerate(btns):
        # 跳过取消、确认按钮，放到最后一行
        if btn.data in ["cancel", "confirm"]:
            continue
        if len(row) >= size or row_len + buttons_len[i] > BUTTON_ROW_MAX_LEN and row:
            result.append(row)
            row = []
            row_len = 0
        row.append(Button.inline(btn.text, btn.data))
        row_len += buttons_len[i]
    if row:
        result.append(row)
    # 确认、取消按钮放到最后一行
    last_row = []
    for btn in btns:
        if btn.data in ["cancel", "confirm"]:
            last_row.append(Button.inline(btn.text, btn.data))
    if last_row:
        result.append(last_row)
    return result


async def wait_btn_callback(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str,
    btns: List[InputButton],
    remove_btn: bool = True,
    timeout: float = 60,
    size: int = 3,
) -> str:
    btns_data = [btn.data for btn in btns]
    # 一行size个按钮
    buttons = buttons_layout(btns, size)

    # 等待用户点击按钮
    async with bot.conversation(
        await event.get_chat(), timeout=timeout, exclusive=False
    ) as conv:
        ans = await conv.send_message(tips_text, buttons=buttons)
        try:
            while True:
                # 等待用户点击按钮
                res = await conv.wait_event(
                    events.CallbackQuery(func=lambda e: e.sender_id == event.sender_id),
                    timeout=timeout,
                )
                # bytes 转字符串
                data: str = res.data.decode()
                if data == CANCEL:
                    raise CancelInput
                if data in btns_data:
                    return data
        finally:
            if remove_btn:
                # 删除按钮
                await ans.delete()


from abc import ABCMeta, abstractmethod


class InputBase(metaclass=ABCMeta):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
    ):
        self.bot = bot
        self.event = event
        self.tips_text = tips_text

    @abstractmethod
    async def input(self) -> Any:
        pass


class CommandInfo:
    def __init__(self, name: str, command: str, description: str):
        self.name = name
        self.command = command
        self.description = description


class CommandField:
    def __init__(
        self,
        key: str,
        name: str,
        description: str,
        command_input: Any,
        value: Any = None,
    ):
        self.key = key
        self.name = name
        self.description = description
        self.command_input = command_input
        self.value = value


class InputText(InputBase):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
    ):
        super().__init__(bot, event, tips_text)

    async def input(
        self,
        placeholder: Optional[str] = None,
        timeout: float = 60,
    ) -> Optional[str]:
        e = await wait_msg_callback(
            self.bot,
            self.event,
            self.tips_text,
            timeout=timeout,
            placeholder=placeholder,
            remove_text=True,
        )
        return str(e.message)


class InputTextInt(InputBase):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
    ):
        super().__init__(bot, event, tips_text)

    async def input(
        self,
        placeholder: Optional[str] = None,
        timeout: float = 60,
    ) -> Optional[int]:
        while True:
            e = await wait_msg_callback(
                self.bot,
                self.event,
                self.tips_text,
                timeout=timeout,
                placeholder=placeholder,
                remove_text=True,
            )
            try:
                return int(e.message)
            except:
                self.tips_text = self.tips_text + ", 请输入正确的整数"


class InputBtns(InputBase):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
        btns: List[InputButton],
    ):
        super().__init__(bot, event, tips_text)
        self.btns = btns

    async def input(
        self, timeout: float = 60, remove_btn: bool = True
    ) -> Union[Optional[str], Any]:
        return await wait_btn_callback(
            self.bot,
            self.event,
            tips_text=self.tips_text,
            btns=self.btns,
            remove_btn=remove_btn,
            timeout=timeout,
        )


class InputBtnsBool(InputBtns):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
        btn_yes_text: str = "True",
        btn_no_text: str = "False",
    ):
        super().__init__(
            bot,
            event,
            tips_text,
            [InputButton(btn_yes_text, "True"), InputButton(btn_no_text, "False")],
        )

    async def input(self, timeout: float = 60, remove_btn: bool = True) -> bool:
        return (await super().input(timeout=timeout, remove_btn=remove_btn)) == "True"


class InputBtnsCancel(InputBtns):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
    ):
        super().__init__(
            bot,
            event,
            tips_text,
            [InputButton("取消", "cancel")],
        )

    async def input(self, timeout: float = 60, remove_btn: bool = True) -> bool:
        return (await super().input(timeout=timeout, remove_btn=remove_btn)) == "cancel"


class InputListStr(InputBtns):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
        old_list: List[str],
    ):
        self.old_list = old_list
        self.tips_text = tips_text + "\n当前列表："
        self.prefix = f"{event.id}_input_btns_old_"
        self.reflush()
        super().__init__(
            bot,
            event,
            tips_text,
            btns=self.btns,
        )

    def reflush(self) -> None:
        self.btns = [
            InputButton(f"{i + 1}. {item}", f"{self.prefix}{i}")
            for i, item in enumerate(self.old_list)
        ]
        self.btns.extend(
            [
                InputButton("新增", f"{self.prefix}add"),
                InputButton("完成", f"{self.prefix}cancel"),
            ]
        )

    def __add_item(self, item: str) -> None:
        self.old_list.append(item)
        self.reflush()

    def __del_item(self, index: int) -> None:
        self.old_list.pop(index)
        self.reflush()

    async def input(self, timeout: float = 60, remove_btn: bool = True) -> List[str]:
        while True:
            data = await super().input(timeout=timeout, remove_btn=remove_btn)
            if not data or data == f"{self.prefix}cancel":
                return self.old_list
            elif data == f"{self.prefix}add":
                try:
                    in_text = await InputText(self.bot, self.event, "请输入").input()
                except CancelInput:
                    continue
                if in_text:
                    self.__add_item(in_text)
            elif data.startswith(self.prefix):
                index = int(data[len(self.prefix) :])
                confirm = await InputBtnsBool(
                    self.bot, self.event, f"{self.old_list[index]}\n确认删除?"
                ).input()
                if confirm:
                    self.__del_item(index)


class InputListInt(InputBtns):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
        old_list: List[int],
        unique: bool = True,
    ):
        self.old_list = old_list
        self.tips_text = tips_text + "\n当前列表(点击删除):"
        self.prefix = f"{event.id}_input_btns_old_"
        self.unique = unique
        self.reflush()
        super().__init__(
            bot,
            event,
            tips_text,
            btns=self.btns,
        )

    def reflush(self) -> None:
        self.btns = [
            InputButton(f"{i + 1}. {item}", f"{self.prefix}{i}")
            for i, item in enumerate(self.old_list)
        ]
        self.btns.extend(
            [
                InputButton("新增", f"{self.prefix}add"),
                InputButton("完成", f"{self.prefix}cancel"),
            ]
        )

    def __add_item(self, item: int) -> None:
        if item in self.old_list and self.unique:
            return
        self.old_list.append(item)
        self.reflush()

    def __del_item(self, index: int) -> None:
        self.old_list.pop(index)
        self.reflush()

    async def input(self, timeout: float = 60, remove_btn: bool = True) -> List[int]:
        while True:
            data = await super().input(timeout=timeout, remove_btn=remove_btn)
            if not data or data == f"{self.prefix}cancel":
                return self.old_list
            elif data == f"{self.prefix}add":
                try:
                    in_text = await InputTextInt(self.bot, self.event, "请输入").input()
                except CancelInput:
                    continue
                if in_text:
                    self.__add_item(in_text)
            elif data.startswith(self.prefix):
                index = int(data[len(self.prefix) :])
                confirm = await InputBtnsBool(
                    self.bot, self.event, f"{self.old_list[index]}\n确认删除?"
                ).input()
                if confirm:
                    self.__del_item(index)
