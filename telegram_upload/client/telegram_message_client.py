import time
from typing import Iterable, Optional

import click
from telethon import TelegramClient
from telethon.errors import RPCError, FloodWaitError, InvalidBufferError
from enum import Enum

RETRIES = 3

class ParsMode(str, Enum):
    HTML = 'html'
    MARKDOWN = 'markdown'
    MD = 'md'


class TelegramMessageClient(TelegramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def forward_to(self, message, destinations):
        for destination in destinations:
            self.forward_messages(destination, [message])

    def send_one_message(self, entity, text_message: str, retries=RETRIES, parse_mode: Optional[ParsMode] = None):
        message = None
        try:
            message = self.send_message(entity, text_message, parse_mode=parse_mode)
        except FloodWaitError as e:
            click.echo(f'{e}. Waiting for {e.seconds} seconds.', err=True)
            time.sleep(e.seconds)
            message = self.send_one_message(entity, text_message, retries=retries, parse_mode=parse_mode)
        except RPCError as e:
            if retries > 0:
                click.echo(f'The message "{text_message}" could not be sent: {e}. Retrying...', err=True)
                message = self.send_one_message(entity, text_message, retries=retries - 1, parse_mode=parse_mode)
            else:
                click.echo(f'The message "{text_message}" could not be sent: {e}. It will not be retried.', err=True)
        return message

    def send_messages(self, entity, text_messages: Iterable[str], parse_mode: Optional[ParsMode] = None, forward=()):
        messages = []
        for text_msg in text_messages:
            try:
                message = self.send_one_message(entity, text_msg, parse_mode = parse_mode)
            finally:
                pass
            if message is None:
                click.echo('Failed to send message "{}"'.format(text_msg), err=True)
            if message:
                self.forward_to(message, forward)
                messages.append(message)
        return messages