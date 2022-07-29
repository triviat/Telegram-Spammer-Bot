from sessions import get_sessions, set_up_sessions, start_sessions

import asyncio
import os


async def check_files() -> bool:
    """Проверяет наличие всех файлов, необходимых для корректной работы."""
    message = list()
    if not os.path.exists('settings.json'):
        message.append('Файл с настройками settings.json не найден.\n')

    if not os.path.exists('message.txt'):
        message.append('Файл с сообщением message.txt не найден.\n')

    if not os.path.exists('./sessions/users.json'):
        message.append('Файл с пользователями /sessions/users.json не найден.\n')

    if message:
        print(*message)
        return False
    else:
        return True


async def main() -> None:
    """
    Сессии телеграмма.
        1. Создание и получение.
        2. Настройка.
        3. Запуск.
    """
    if not await check_files():
        return

    sessions = await get_sessions()
    if len(sessions) != 0:
        print(f'Найдено и создано {len(sessions)} сессий')
    else:
        print('Сессии телеграмм не найдены.')
        return

    await set_up_sessions(len(sessions))
    await start_sessions(sessions)

    return


if __name__ == '__main__':
    try:
        try:
            asyncio.run(main())
        finally:
            input()
    except KeyboardInterrupt:
        pass
