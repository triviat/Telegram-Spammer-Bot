import telethon.errors.rpcerrorlist
from telethon import TelegramClient, events
from telethon.tl import types
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest

import json
import os
import asyncio
import random

replied_users = list()
count_sent = 0
session_blocked = list()
MAX_BLOCKED = 2


async def get_sessions() -> list:
    """Получение клиентов сессий телеграмма"""

    path = f'./sessions/users.json'

    if os.path.exists(path):
        configs = await get_user_configs(path)
    else:
        return []

    sessions = list()
    for config in configs:
        sessions.append(await create_session(config))

    return sessions


async def create_session(config: dict) -> TelegramClient:
    """Создание и запуск клиента телеграмм"""
    print(f'[{config["session_name"]}] Авторизация...')

    client = TelegramClient(config['session_name'], config['api_id'], config['api_hash'])

    if config.get('proxy', False):
        try:
            print(f'[{config["session_name"]}] Подключение к прокси...')
            client.set_proxy(config['proxy'])
            print(f'[{config["session_name"]}] Прокси успешно установлены.')
        except Exception as exc:
            print(f'[{config["session_name"]}] Произошла ошибка при установке прокси.')
            print(f'[ERROR] {exc}')

    await client.start(phone=config['phone'])
    print(f'[{config["session_name"]}] Авторизация прошла успешно.')
    return client


async def get_user_configs(path: str) -> list:
    with open(path) as f:
        return json.load(f)


async def get_delay() -> float:
    while True:
        try:
            delay = float(input('С какой задержкой отправлять сообщения? Введите значение в секундах: ').strip())
            print()
            return delay
        except ValueError:
            print('Неверный ввод. Введите число.')


async def get_direction() -> int:
    """
        Получение направления сообщений (пользователи/группы)

        1 - Пользователям

        2 - В группы
    """
    while True:
        choice = input('Куда отправлять сообщения?\n1. Пользователям\n2. В группы\n').strip()
        if choice == '1':
            if await check_targets_file():
                print('Установлена отправка Пользователям.')
                return 1

        elif choice == '2':
            if await check_targets_file():
                print('Установлена отправка в Группы.')
                return 2

        else:
            print('Неверный ввод. Введите число 1 или 2.')
            continue

        print('Файл targets.txt не найден.')


async def check_targets_file() -> bool:
    return os.path.exists('targets.txt')


async def get_message_type() -> int:
    """
        Получение откуда сообщения (шаблон/репост)

        1 - Шаблон

        2 - Репост
    """
    while True:
        choice = input('Какое сообщение отправлять?\n1. Шаблон\n2. Репост\n').strip()
        if choice == '1':
            if await check_message_file():
                print('Установлена отправка Шаблоном.')
                return 1

        elif choice == '2':
            if await check_message_file():
                print('Установлена отправка Репостом.')
                return 2

        else:
            print('Неверный ввод. Введите число 1 или 2.')
            continue

        print('Файл message.txt не найден.')


async def check_message_file() -> bool:
    return os.path.exists('message.txt')


async def get_auto_reply_status() -> int:
    """
        Получение статуса автоответчика (вкл/выкл)

        1 - Включить

        2 - Выключить
    """
    while True:
        choice = input('Включить автоответчик?\n1. Да\n2. Нет\n').strip()
        if choice == '1':
            if await check_autoreply_file():
                print('Автоответчик включен.')
                return 1
            else:
                print('Файл autoreply.txt не найден.')
        elif choice == '2':
            print('Автоответчик отключен.')
            return 2
        else:
            print('Неверный ввод. Введите число 1 или 2.')


async def check_autoreply_file() -> bool:
    return os.path.exists('autoreply.txt')


async def set_up_sessions(session_count: int) -> None:
    """
        Получает и возвращает:
            1. Куда отправлять сообщения
            2. Откуда брать сообщения
            3. Статус автоответчика
    """

    settings = await get_settings()

    delay = settings.get('delay', {})
    direction = settings.get('direction', {})
    message_type = settings.get('message_type', {})
    auto_reply = settings.get('auto_reply', {})

    while True:
        if delay and direction and message_type and auto_reply:

            print(f'\nНайдены старые настройки:\n'
                  f'\tЗадержка между сообщениями: {delay} секунд\n'
                  f'\tКуда отправлять: {"пользователям" if direction == 1 else "в группы"}\n'
                  f'\tЧто отправлять: {"шаблон" if message_type == 1 else "репост"}\n'
                  f'\tАвтоответчик: {"включен" if auto_reply == 1 else "выключен"}\n')

            choice = input('Использовать прошлые установки? (1 - да, 2 - нет) ').strip()
            if choice == '1':
                return
            elif choice == '2':
                print('Тогда начнем настройку')
                break
            else:
                print('Неверный ввод. Введите число 1 или 2.')

    while True:
        delay = await get_delay()
        direction = await get_direction()
        message_type = await get_message_type()
        auto_reply = await get_auto_reply_status()

        print(f'Установлены следующие настройки:\nКоличество сессий: {session_count}\n'
              f'Задержка между сообщениями: {delay} секунд\n'
              f'Куда отправлять: {"пользователям" if direction == 1 else "в группы"}\n'
              f'Что отправлять: {"шаблон" if message_type == 1 else "репост"}\n'
              f'Автоответчик: {"включен" if auto_reply == 1 else "выключен"}')

        while True:
            is_ok = input('Все правильно? (1 - да, 2 - нет): ')
            if is_ok == '1':
                print('Настройки установлены.')
                await save_settings(delay=delay,
                                    direction=direction,
                                    message_type=message_type,
                                    auto_reply=auto_reply)
                return
            elif is_ok == '2':
                print('Тогда начнем сначала.')
                break
            else:
                print('Неверный ввод. Введите число 1 или 2.')


async def start_sessions(sessions: list) -> None:
    settings = await get_settings()

    if settings['auto_reply'] == 1:
        for session in sessions:
            me = await session.get_me()
            replied_users.append(me.id)

            session.add_event_handler(reply, events.NewMessage)

    for _ in await asyncio.gather(
            *[start_sending_message(sessions[i], i, len(sessions)) for i in range(len(sessions))]):
        pass


async def get_auto_reply_string() -> str:
    with open('autoreply.txt', encoding='UTF-8') as f:
        return '\n'.join([line.strip() for line in f.readlines()])


async def reply(event: events.NewMessage.Event):
    try:
        if event.is_private and (event.message.peer_id.user_id not in replied_users) and \
                ((await event.client.get_me()).id != event.message.from_id.user_id):
            user_id = event.message.from_id.user_id
            name = ''.join(event.client.__dict__['session'].filename.split('.')[:-1])

            replied_users.append(user_id)
            await event.message.reply(await get_auto_reply_string())

            print(f'[{name}] Ответил на сообщение.')
    except Exception as exc:
        name = ''.join(event.client.__dict__['session'].filename.split('.')[:-1])
        print(f'[{name}] Столкнулся с ошибкой. {exc}')


async def start_sending_message(session: TelegramClient, queue_number: int, queue_step: int) -> None:
    global count_sent, session_blocked

    settings = await get_settings()
    direction = settings['direction']
    message_type = settings['message_type']
    delay = settings['delay']
    name = ''.join(session.__dict__['session'].filename.split('.')[:-1])

    message_entity = await get_message_entity(session, settings['message_type'])
    if message_entity is None:
        print(f'[{name}] Не смог найти сообщение для отправки.')
        return

    targets = await get_targets_list()
    max_targets = len(targets)
    if queue_number > max_targets:
        if settings['auto_reply'] == 1:
            print(f'[{name}] Встал в режим автоответчика.')
        return

    print(f'[{name}] Начал отправку сообщений.')

    # Отправка шаблоном пользователям
    if message_type == 1 and direction == 1:
        for target in range(queue_number, len(targets), queue_step):
            try:
                if len(session_blocked) >= MAX_BLOCKED:
                    session.disconnect()
                    print(f'[STOP] [{name}] Было заблокировано {len(session_blocked)} аккаунтов.')

                    with open('bad_users.txt', 'a') as f:
                        for i in range(target, len(targets), queue_step):
                            f.write(targets[i]+'\n')
                    break
                message = message_entity[random.randint(0, len(message_entity)-1)]
                await session.send_message(entity=targets[target], message=message)

                count_sent += 1
                print(f'[{count_sent}/{max_targets}] - [{name}] Отправил сообщение и ждет {delay} секунд.')
                await asyncio.sleep(delay)
            except telethon.errors.rpcerrorlist.PhoneNumberBannedError:
                session_blocked.append(name)
                print(f'[ERROR] [{name}] Номер заблокирован и прекратил рассылку.')
                session.disconnect()

                with open('bad_users.txt', 'a') as f:
                    for i in range(target, len(targets), queue_step):
                        f.write(targets[i]+'\n')
                break
            except Exception as exception:
                if 'A wait of ' in str(exception):
                    pause_time = int(str(exception).split()[3])
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}\n'
                          f'И уходит в спячку на {pause_time} секунд.')
                    await asyncio.sleep(pause_time)
                else:
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}')
                with open('bad_users.txt', 'a') as f:
                    f.write(targets[target]+'\n')

    # Отправка шаблоном в группы
    elif message_type == 1 and direction == 2:
        for target in range(queue_number, len(targets), queue_step):
            try:
                if len(session_blocked) >= MAX_BLOCKED:
                    session.disconnect()
                    print(f'[STOP] [{name}] Было заблокировано {MAX_BLOCKED} или более аккаунтов.')

                    with open('bad_users.txt', 'a') as f:
                        for i in range(target, len(targets), queue_step):
                            f.write(targets[i]+'\n')
                    break

                result = await session(ResolveUsernameRequest(targets[target].split('/')[-1]))
                channel = types.InputChannel(result.peer.channel_id, result.chats[0].access_hash)
                await session(JoinChannelRequest(channel))

                message = message_entity[random.randint(0, len(message_entity)-1)]
                await session.send_message(entity=targets[target], message=message)

                count_sent += 1
                print(f'[{count_sent}/{max_targets}] - [{name}] Отправил сообщение и ждет {delay} секунд.')
                await asyncio.sleep(delay)
            except telethon.errors.rpcerrorlist.PhoneNumberBannedError:
                session_blocked.append(name)
                print(f'[ERROR] [{name}] Номер заблокирован и прекратил рассылку.')
                session.disconnect()

                with open('bad_users.txt', 'a') as f:
                    for i in range(target, len(targets), queue_step):
                        f.write(targets[i]+'\n')
                break
            except Exception as exception:
                if 'A wait of ' in str(exception):
                    pause_time = int(str(exception).split()[3])
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}\n'
                          f'И уходит в спячку на {pause_time} секунд.')
                    await asyncio.sleep(pause_time)
                else:
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}')
                with open('bad_users.txt', 'a') as f:
                    f.write(targets[target]+'\n')

    # Отправка репостом пользователям
    elif message_type == 2 and direction == 1:
        for target in range(queue_number, len(targets), queue_step):
            try:
                if len(session_blocked) >= MAX_BLOCKED:
                    session.disconnect()
                    print(f'[STOP] [{name}] Было заблокировано {MAX_BLOCKED} или более аккаунтов.')

                    with open('bad_users.txt', 'a') as f:
                        for i in range(target, len(targets), queue_step):
                            f.write(targets[i]+'\n')
                    break

                if isinstance(message_entity, types.Message):
                    await session.forward_messages(targets[target], message_entity)

                count_sent += 1
                print(f'[{count_sent}/{max_targets}] - [{name}] Отправил сообщение и ждет {delay} секунд.')
                await asyncio.sleep(delay)
            except telethon.errors.rpcerrorlist.PhoneNumberBannedError:
                session_blocked.append(name)
                print(f'[ERROR] [{name}] Номер заблокирован и прекратил рассылку.')
                session.disconnect()

                with open('bad_users.txt', 'a') as f:
                    for i in range(target, len(targets), queue_step):
                        f.write(targets[i]+'\n')
                break
            except Exception as exception:
                if 'A wait of ' in str(exception):
                    pause_time = int(str(exception).split()[3])
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}\n'
                          f'И уходит в спячку на {pause_time} секунд.')
                    await asyncio.sleep(pause_time)
                else:
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}')
                with open('bad_users.txt', 'a') as f:
                    f.write(targets[target]+'\n')

    # Отправка репостом в группы
    elif message_type == 2 and direction == 2:
        for target in range(queue_number, len(targets), queue_step):
            try:
                if len(session_blocked) >= MAX_BLOCKED:
                    session.disconnect()
                    print(f'[STOP] [{name}] Было заблокировано {MAX_BLOCKED} или более аккаунтов.')

                    with open('bad_users.txt', 'a') as f:
                        for i in range(target, len(targets), queue_step):
                            f.write(targets[i]+'\n')
                    break

                result = await session(ResolveUsernameRequest(targets[target].split('/')[-1]))
                channel = types.InputChannel(result.peer.channel_id, result.chats[0].access_hash)
                await session(JoinChannelRequest(channel))

                if isinstance(message_entity, types.Message):
                    await session.forward_messages(targets[target], message_entity)

                count_sent += 1
                print(f'[{count_sent}/{max_targets}] - [{name}] Отправил сообщение и ждет {delay} секунд.')
                await asyncio.sleep(delay)
            except telethon.errors.rpcerrorlist.PhoneNumberBannedError:
                session_blocked.append(name)
                print(f'[ERROR] [{name}] Номер заблокирован и прекратил рассылку.')
                session.disconnect()

                with open('bad_users.txt', 'a') as f:
                    for i in range(target, len(targets), queue_step):
                        f.write(targets[i]+'\n')
                break
            except Exception as exception:
                if 'A wait of ' in str(exception):
                    pause_time = int(str(exception).split()[3])
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}\n'
                          f'И уходит в спячку на {pause_time} секунд.')
                    await asyncio.sleep(pause_time)
                else:
                    print(f'[{name}] Столкнулся с ошибкой. [ERROR] {exception}')
                with open('bad_users.txt', 'a') as f:
                    f.write(targets[target]+'\n')

    if settings['auto_reply'] == 1:
        print(f'[{name}] Закончил отправку сообщений. И встал в режим автоответчика.')
        await session.run_until_disconnected()
    else:
        await session.disconnect()
        print(f'[{name}] Закончил отправку сообщений.')

    if len(session_blocked) > 0:
        session_blocked_string = "\n".join(session_blocked)
        print(f'\nБыли заблокированы:\n{session_blocked_string}')


async def get_targets_list() -> list:
    with open('targets.txt', encoding='UTF-8') as f:
        return [line.strip() for line in f.readlines()]


async def get_message_string() -> str:
    with open('message.txt', encoding='UTF-8') as f:
        return '\n'.join([line.strip() for line in f.readlines()])


async def get_message_entity(session: TelegramClient, message_type: int) -> list or types.Message or None:
    message_string = await get_message_string()
    if message_type == 1:
        return [message.strip() for message in message_string.split('|')]
    else:
        try:
            channel_entity = await session.get_entity('/'.join(message_string.split('/')[:-1]))
            message_id = int(message_string.split('/')[-1])

            for message in await session.get_messages(channel_entity, limit=1000):
                if message.id == message_id:
                    return message
        except ValueError as exception:
            name = ''.join(session.__dict__['session'].filename.split('.')[:-1])
            print(f'[{name}] Столкнулся с ошибкой. {exception}')
        except Exception as exception:
            name = ''.join(session.__dict__['session'].filename.split('.')[:-1])
            print(f'[{name}] Столкнулся с ошибкой. {exception}')


async def get_settings() -> dict:
    with open('settings.json', encoding='UTF-8') as f:
        return json.load(f)


async def save_settings(**kwargs) -> None:
    with open('settings.json', encoding='UTF-8') as f:
        settings = json.load(f)

    for key, value in kwargs.items():
        settings[key] = value

    with open('settings.json', 'w', encoding='UTF-8') as f:
        json.dump(settings, f, indent=4)
