import os

from aiogram.types import FSInputFile
from app.commands import *
from aiogram.filters import Command
from aiogram import types, Router

from app.db.database import SQLBase
from bot import sq

from functools import wraps

rout = Router()
db = sq


def authorized_only(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        if not authorization(message.from_user.id):
            await message.reply("У вас нет прав на выполнение этой команды.")
            return
        return await func(message, *args, **kwargs)
    return wrapper


@rout.message(Command('cm'))
@authorized_only
async def execute(message: types.Message):
    args = message.text.replace('/cm', '').split()

    if args[0] == 'dnw':
        file_path = '/usr/bot/' + args[1]
        if not os.path.exists(file_path):
            await message.answer(f"Файл не найден: {file_path}")
            return
        else:
            try:
                file = FSInputFile(file_path)
                await message.answer_document(file)
            except Exception as e:
                await message.answer(f'{e}')
            finally:
                return

    return await message.answer(execute_cmd(args))


@rout.message(Command('log'))
@authorized_only
async def logout(message: types.Message):
    with open(settings.Global.log_file, 'r') as file:
        file = [x for x in file.readlines()]
        if len(file) >= 11:
            await message.answer(f'{file[-10:]}')
        else:
            await message.answer(f'{[x for x in file]}')


@rout.message(Command('commands'))
@authorized_only
async def commands(message: types.Message):
    return await message.answer('\n'.join([command for command in COMMANDS]))


@rout.message(Command("ips"))
@authorized_only
async def get_ips(message: types.Message):
    args = message.text.replace("/ips", "").strip().split()
    if args:
        port = int(args[0])
        await message.answer(f"{generate_ip_report(port)}", parse_mode="Markdown")
    else:
        await message.answer(f'Неправильный ввод.\n`/ips` _номер порта_')


@rout.message(Command("mark"))
@authorized_only
async def markup(message: types.Message):
    args = message.text.replace("/mark", "").strip().split()
    port = args[0]
    mark = ' '.join(str(x) for x in args[1:])

    if len(args) < 2:
        await message.reply("Ошибка формата. Правильное применение /mark <port> <info>")
        return

    await SQLBase.update_port_mark(port, mark)

    await message.reply(f"Пользователь с портом `{port}` обновил метку на `{mark}`", parse_mode='Markdown')


@rout.message(Command("start"))
@authorized_only
async def send_welcome(message: types.Message):
    await db.create_db()
    await message.reply("Привет!")


@rout.message(Command("stats"))
@authorized_only
async def stats_command(message: types.Message):
    args = message.text.replace('/stats', '').strip().split()

    if args:
        param = args[0]
        await message.answer(f'{get_statistic(param)}', parse_mode='Markdown')
    else:
        await message.answer(f'{get_statistic()}', parse_mode='Markdown')


@rout.message(Command("rule"))
@authorized_only
async def port_de_acivate(message: types.Message):
    args = message.text.replace("/rule", "").strip().split()

    if len(args) < 2:
        await message.reply("Ошибка формата: /rule <port> <1 or 0> #\n1 - Заблокировать\n0 - Разблокировать")
        return

    port, flag = args[0], args[1]

    try:
        if flag == "1":
            subprocess.run(["sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", port, "-j", "DROP"],
                            check=True)
            await message.reply(f"Порт `{port}` заблокирован", parse_mode='Markdown')

            await db.update_flag_by_port(port, flag)

        elif flag == "0":
            subprocess.run(["sudo", "iptables", "-D", "INPUT", "-p", "tcp", "--dport", port, "-j", "DROP"],
                            check=True)
            await message.reply(f"Порт `{port}` разблокирован", parse_mode='Markdown')

            await db.update_flag_by_port(port, flag)

    except subprocess.CalledProcessError as e:
        await message.reply(f"Ошибка выполнения команды: {e}")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")


@rout.message(Command("ssr"))
@authorized_only
async def generate_ssr_link(message: types.Message):
    args = message.text.replace("/ssr", "").strip().split()

    try:
        port = args[-1]
        ssr_key = await db.get_ssr(port)

        if args[0] == "qr":
            photo = generate_qr_code(ssr_key)
            await message.answer_photo(photo)
        elif args[0] == "key":
            await message.reply(f'`{ssr_key}`', parse_mode="Markdown")

    except Exception as e:
        await message.answer(f'Пользователя с таким портом - нет.\n{e}')


@rout.message(Command("adduser"))
@authorized_only
async def add_user_command(message: types.Message):
    try:
        args = message.text.replace("/adduser", "").strip().split()

        if len(args) < 1:
            await message.reply("Ошибка: недостаточно аргументов. Формат команды: /adduser <порт>")
            return

        port = int(args[0])  # Извлечение порта из списка и преобразование в целое число
        if port in await db.get_user_ports():
            await message.reply(f"Пользователь с портом `{port}` уже есть.", parse_mode='Markdown')
            return

        password = await db.add_user(port)
        await message.reply(f"Пользователь добавлен: с портом `{port}` и паролем `{password}`",
                                parse_mode="Markdown")
    except ValueError:
        await message.reply("Ошибка: порт должен быть целым числом.")
    except Exception as e:
        await message.answer(f'Ошибка: {e}')


@rout.message(Command("removeuser"))
@authorized_only
async def remove_user_command(message: types.Message):
    args = message.text.replace("/removeuser", "").strip().split()

    if not args:
        await message.reply("Использование: /removeuser <порт>")
        return

    try:
        port = int(args[0])
        await db.remove_user(port)
        await message.reply(f"Пользователь с портом `{port}` удален!", parse_mode='Markdown')
    except ValueError:
        await message.reply("Ошибка: порт должен быть числом.")


@rout.message(Command("listusers"))
@authorized_only
async def list_users_command(message: types.Message):
    users = await db.list_users()
    if users:
        user_list = "\n".join([f"Порт: `{user[1]}` "
                                   f"Пароль: `{user[2]}` "
                                   f"Флаг: `{user[6]}` "
                                   f"Метка: `{user[5]}` \n" for user in users])
        await message.reply(f"Список пользователей:\n{user_list}", parse_mode='Markdown')
    else:
        await message.reply("Нет пользователей.")


@rout.message(Command("online"))
@authorized_only
async def active_connections_command(message: types.Message):
    connections = get_connections()
    user_ports = await db.get_user_ports()

    pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b:\b\d+\b"
    matches = re.findall(pattern, connections)

    filtered_connections = [
            match for match in matches if match.split(':')[-1] in map(str, user_ports)
        ]

    if not filtered_connections:
        await message.reply("Нет активных подключений.")

    result = filtered_connections
    cur_ip = []
    raport = []

    for ip in result:
        for port in user_ports:
            if str(port) in ip and ip not in cur_ip:
                cur_ip.append(ip)

    for user in cur_ip:
        for cur_port in user_ports:
            if str(cur_port) in user:
                device_counts = len(get_connected_ips(cur_port))
                user_mark = await db.find_mark_by_port(cur_port)

                raport.append(f"Адрес: `{user}`\n"
                                  f"Пользователь: `{user_mark}`\n"
                                  f"C `{device_counts}` дата центра\n")
    raport_str = '\n'.join(raport)

    await message.answer(raport_str, parse_mode='Markdown')


@rout.message(Command("stop"))
@authorized_only
async def stop_bot(message: types.Message):
    from bot import stop
    await message.reply("Гудбай")
    await stop()
