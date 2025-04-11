import base64
import subprocess
import re
from io import BytesIO

import qrcode
import requests
from aiogram.types import BufferedInputFile

from settings import settings

import random
import string

DATABASE_URL = settings.Db.url

COMMANDS = ['/online',
            '/cm <command>',
            '/listusers',
            '/ips <port>',
            '/adduser <port>',
            '/removeuser <port>',
            '/rule <port> <1 - ban | 0 - unban>',
            '/ssr <port> <qr key>',
            '/stats | <-h -d -m>',
            '/mark <port> <info>'
            '/start']


def authorization(user_id: int) -> bool:
    if user_id == settings.Secure.admin_id:
        return True
    else:
        return False


def generate_password(length=8):
    characters = string.ascii_letters + string.digits

    password = ''.join(random.choice(characters) for _ in range(length))

    return password


def generate_qr_code(data: str) -> BufferedInputFile:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)

        buffer = BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(buffer)
        buffer.seek(0)

        return BufferedInputFile(buffer.read(), filename="qr_code.png")


def generate_ssr(port, password):
    ip = settings.Secure.ip
    method = settings.Secure.method
    protocol = settings.Secure.protocol
    obfs = settings.Secure.obfs
    user_info = f"{ip}:{port}:{protocol}:{method}:{obfs}:{base64.urlsafe_b64encode(password.encode()).decode().strip('=')}"
    return f"ssr://{base64.urlsafe_b64encode(user_info.encode()).decode().strip('=')}"


def get_connections():
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Ошибка: netstat завис"
    except Exception as e:
        return f"Ошибка: {e}"


def get_connected_ips(port):
    # Выполняем команду ss с фильтром по порту
    result = subprocess.run(
        f'sudo ss -tnp | grep ":{port} "',  # Фильтр по указанному порту
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.stderr:
        print("Error:", result.stderr)
        return []

    ip_pattern = r'(\d+\.\d+\.\d+\.\d+)|\[::ffff:(\d+\.\d+\.\d+\.\d+)\]'

    ips = []
    for line in result.stdout.splitlines():
        columns = line.split()
        if len(columns) >= 5:
            remote_address = columns[4]
            match = re.search(ip_pattern, remote_address)
            if match:
                ips.append(match.group(1) or match.group(2))

    return set(ips)


def get_ip_info(ip_address):
    url = f"https://api.iplocation.net/?ip={ip_address}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("response_code") == "200":
            return data
        else:
            print(f"Error: {data.get('response_message')}")
            return None
    except requests.RequestException as e:
        print(f"Error connecting to API: {e}")
        return None


def generate_ip_report(port):
    connected_ips = get_connected_ips(port)
    if not connected_ips:
        return "Нет подключений"

    ip_info_list = []
    for ip in connected_ips:
        ip_data = get_ip_info(ip)
        if ip_data:
            ip_info_list.append(
                f"IP: `{ip_data['ip']}`\n"
                f"ISP: `{ip_data['isp']}`\n"
                f"Country: `{ip_data['country_code2']}`\n"
            )

    if ip_info_list:
        report = "\n".join(ip_info_list)
        return report
    else:
        return "Не удалось получить информацию"


def get_statistic(param=None):
    args = ['vnstat', param]
    if param is None:
        args = ['vnstat']

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5).stdout
        result = result.replace('GiB', 'GB').replace('TiB', 'TB')
        return result

    except subprocess.TimeoutExpired:
        return "Ошибка: vnstat завис"

    except Exception as e:
        return f"Ошибка: {e}"


def execute_cmd(command: list):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception as e:
        return f'Ошибка выполнения\n\n{e}'
