import re
import asyncio
from sys import stdout
from os.path import exists

from telethon import TelegramClient
from telethon.tl.types import Channel

DEVICE_META = {
    'device_model': 'Samsung SM-A707F',
    'system_version': 'SDK 31',
    'app_version': '10.6.4 (106040)',
    'lang_code': 'en',
    'system_lang_code': 'en-us',
}


def progress_bar(current: int, total: int) -> None:
    filled = int(30 * current // total)
    stdout.write(
        f"\r  |{'█' * filled}{'-' * (30 - filled)}| "
        f"{100 * (current / total):.1f}%"
    )
    stdout.flush()


def ask_with_check(
    input_msg: str,
    warn_msg: str,
    regex: str | re.Pattern[str],
) -> str:
    while True:
        user_input = input(input_msg).strip()
        if re.match(regex, user_input):
            break
        print(warn_msg)

    return user_input


def ask_api_conf():
    api_id = ask_with_check(
        'Please enter your API ID: ',
        'Invalid format! Example: 12345678',
        r'\d+'
    )

    api_hash = ask_with_check(
        'Please enter your API HASH: ',
        'Invalid format! Example: 478785e68198f61365590bcf4411e0d5',
        r'[\da-f]+'
    )

    return int(api_id), api_hash


async def main():
    api_id, api_hash = (
        ask_api_conf()
        if not exists('telegram.session')
        else 1, 'a'
    )

    client = TelegramClient(
        session='telegram',
        api_id=api_id,
        api_hash=api_hash,
        **DEVICE_META,
    )

    await client.start()
    await client.get_dialogs()

    while True:
        link = ask_with_check(
            '> Enter the link to a message: ',
            'Invalid format! Example: https://t.me/durov/123',
            r'https://t\.me/\w+/\d+',
        )

        chat_id, msg_id = link.split('/')[-2:]

        chat = await client.get_entity(
            int(chat_id) if chat_id.isdigit() else chat_id
        )

        if not chat:
            print('  <Chat not found>')
            continue

        if not isinstance(chat, Channel):
            print('  <Peer is not a chat/channel>')
            continue

        message = await client.get_messages(chat, ids=int(msg_id))
        if not message:
            print('  <Message not found>')
            continue

        date = message.date.strftime('%Y-%m-%d %H:%M')
        text = (
            message.message[:35].replace('\n', ' ')
            + '...' * (len(message.message) > 35)
        )
        media = (
            message.media.to_dict()['_']
            .removeprefix('MessageMedia')
        ) if message.media else None

        print(f'  [{date}] {text}')

        if not media:
            print('  <No media found>')
            continue

        yn = input(
            f'  <Found {media} in message> Download it? (Y/n) '
        ).lower().strip()

        while yn not in ('', 'y', 'n'):
            yn = input(f'  Type \'y\' (yes) or \'n\' (no) ').lower().strip()

        if yn == 'n':
            continue

        await client.download_media(
            message, './',
            progress_callback=progress_bar,
        )
        print()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nGoodbye!')
