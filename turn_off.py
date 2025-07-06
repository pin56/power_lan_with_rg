# Скрипт для выключения компьютера при получении Wake-on-LAN пакета
# Слушает UDP порт 9 и при получении правильного WoL пакета выключает систему

import socket
import os
import logging
import psutil
import time
import json
import threading
from dotenv import load_dotenv

load_dotenv()

SERVER_MAC_ADDRESS = os.getenv("SERVER_MAC_ADDRESS")
BROADCAST_IP = os.getenv("BROADCAST_IP")



# Константы
WOL_PORT = 9  # Стандартный порт для Wake-on-LAN
INTERFACE_NAME = 'en0'  # Имя сетевого интерфейса для мониторинга
TIME_PORT = 59681 # Порт для отправки времени

# Настройка логирования
logging.basicConfig(format='%(levelname)s: %(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



def get_ip_mac_address(interface_name: str) -> tuple:
    """
    Получает IP и MAC адрес указанного сетевого интерфейса
    
    Args:
        interface_name (str): Имя сетевого интерфейса
        
    Returns:
        tuple: (ip_address, mac_address) - кортеж с IP и MAC адресами
        
    Raises:
        Exception: Если не удалось получить адреса
    """
    ip_addr = mac_addr = None

    # Перебираем все адреса указанного интерфейса
    for item in psutil.net_if_addrs()[interface_name]:
        addr = item.address

        # В IPv4-адресах разделители - точки
        if '.' in addr:
            ip_addr = addr
        # В MAC-адресах разделители либо тире, либо одинарное двоеточие.
        # Двойное двоеточие - это разделители для адресов IPv6
        elif ('-' in addr or ':' in addr) and '::' not in addr:
            # Приводим MAC-адрес к одному формату. Формат может меняться в зависимости от ОС
            mac_addr = addr.replace(':', '-').upper()

    # Проверяем, что получили валидные адреса
    if not ip_addr or not mac_addr or ip_addr == '127.0.0.1':
        raise Exception('Не удалось получить IP или MAC-адрес сетевого интерфейса')

    return ip_addr, mac_addr


def assemble_off_packet(mac_address: str) -> str:
    """
    Собирает строку Wake-on-LAN пакета для сравнения
    
    WoL пакет состоит из:
    - 6 байт 0xFF (магическая последовательность)
    - 16 повторений MAC-адреса (96 байт)
    
    Args:
        mac_address (str): MAC-адрес в формате XX-XX-XX-XX-XX-XX
        
    Returns:
        str: Строка WoL пакета для сравнения
    """
    return f'{"00-" * 6}{(mac_address + "-") * 16}'


def assemble_sleep_packet(mac_address: str) -> str:
    """
    Собирает строку Wake-on-LAN пакета для сравнения
    
    WoL пакет состоит из:
    - 6 байт 0xFF (магическая последовательность)
    - 16 повторений MAC-адреса (96 байт)
    
    Args:
        mac_address (str): MAC-адрес в формате XX-XX-XX-XX-XX-XX
        
    Returns:
        str: Строка WoL пакета для сравнения
    """
    return f'{"99-" * 6}{(mac_address + "-") * 16}'

def check_is_wol_packet(raw_bytes: bytes, assembled_wol_packet: str) -> int:
    """
    Проверяет, является ли полученный пакет Wake-on-LAN пакетом
    
    Args:
        raw_bytes (bytes): Сырые байты полученного пакета
        assembled_wol_packet (str): Ожидаемый WoL пакет для сравнения
        
    Returns:
        int: 1 если это WoL пакет, 0 если нет
    """
    # Преобразуем байты в строку в формате XX-XX-XX-XX...
    decoded_packet_data = '-'.join(f'{byte:02x}' for byte in raw_bytes).upper() + '-'

    # Сравниваем с ожидаемым пакетом
    if decoded_packet_data == assembled_wol_packet:
        return 1

    return 0

def run_udp_port_listener_time(port: int, interface_name: str):
    """
    Основная функция - слушает время, для отправки в сообщения
    
    Args:
        port (int): UDP порт для прослушивания
        interface_name (str): Имя сетевого интерфейса
    """
    # Получаем IP и MAC адрес интерфейса
    ip_addr, mac_addr = get_ip_mac_address(interface_name)

    # Создаем UDP сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((ip_addr, port))
    logger.info(f'Listening on {ip_addr}:{port}')

    # Бесконечный цикл прослушивания
    while True:
        # Получаем данные из сокета
        data, _ = server_socket.recvfrom(1024)
        decoded_packet_data = '-'.join(f'{byte:02x}' for byte in data).upper() + '-'

        return data, decoded_packet_data

def run_udp_port_listener_lan(port: int, interface_name: str):
    """
    Основная функция - слушает UDP порт и выключает компьютер при получении WoL пакета
    
    Args:
        port (int): UDP порт для прослушивания
        interface_name (str): Имя сетевого интерфейса
    """
    # Получаем IP и MAC адрес интерфейса
    ip_addr, mac_addr = get_ip_mac_address(interface_name)

    # Создаем UDP сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((ip_addr, port))
    logger.info(f'Listening on {ip_addr}:{port}')

    # Собираем ожидаемый WoL пакет
    assembled_off_packet = assemble_off_packet(mac_addr)
    assembled_sleep_packet = assemble_sleep_packet(mac_addr)

    # Бесконечный цикл прослушивания
    while True:
        # Получаем данные из сокета
        data, _ = server_socket.recvfrom(1024)

        # Проверяем, является ли пакет WoL пакетом
        is_wol_packet = check_is_wol_packet(data, assembled_off_packet)
        is_sleep_packet = check_is_wol_packet(data, assembled_sleep_packet)
        # Если это WoL пакет - выключаем компьютер или засыпаем
        if is_sleep_packet == 1:
            if os.name == 'posix':  # Linux/Unix системы
                os.system('sudo systemctl suspend')
            elif os.name == 'nt':   # Windows системы
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        elif is_wol_packet == 1:
            if os.name == 'posix':  # Linux/Unix системы
                os.system('sudo shutdown -h now')
            elif os.name == 'nt':   # Windows системы
                os.system('shutdown -s -t 0 -f')



def get_system_uptime() -> dict:
    """
    Получает время работы системы в различных форматах
    
    Returns:
        dict: Словарь с временем работы системы
    """
    # Получаем время загрузки системы
    boot_time = psutil.boot_time()
    current_time = time.time()
    uptime_seconds = current_time - boot_time
    
    # Конвертируем в различные форматы
    uptime_hours = uptime_seconds / 3600
    uptime_days = uptime_hours / 24
    
    return {
        'uptime_seconds': int(uptime_seconds),
        'uptime_hours': round(uptime_hours, 2),
        'uptime_days': round(uptime_days, 2),
        'boot_time': int(boot_time),
        'current_time': int(current_time),
        'formatted_uptime': f"{int(uptime_days)}d {int(uptime_hours % 24)}h {int((uptime_seconds % 3600) / 60)}m {int(uptime_seconds % 60)}s"
    }

def send_time_to_server(mac_address: str, broadcast_ip: str = "192.168.50.255", port: int = TIME_PORT):
    """
    Отправляет время работы системы на сервер
    
    Args:
        mac_address (str): MAC-адрес сервера
        broadcast_ip (str): Broadcast IP адрес
        port (int): Порт для отправки
    """
    try:
        # Получаем время работы системы
        uptime_data = get_system_uptime()
        
        # Добавляем MAC-адрес отправителя
        uptime_data['sender_mac'] = mac_address
        
        # Конвертируем в JSON
        time_message = json.dumps(uptime_data, ensure_ascii=False)
        
        # Отправка UDP broadcast
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(time_message.encode('utf-8'), (broadcast_ip, port))
            
        logger.info(f"Отправлено время работы системы: {uptime_data['formatted_uptime']}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке времени: {e}")

def send_uptime_command():
    """
    Команда для отправки времени работы системы
    """
    if not SERVER_MAC_ADDRESS or not BROADCAST_IP:
        logger.error("Не установлены переменные окружения SERVER_MAC_ADDRESS или BROADCAST_IP")
        return
    
    send_time_to_server(SERVER_MAC_ADDRESS, BROADCAST_IP, TIME_PORT)

def send_uptime_periodically(interval_seconds: int = 5):
    """
    Периодически отправляет время работы системы
    
    Args:
        interval_seconds (int): Интервал отправки в секундах
    """
    while True:
        try:
            send_uptime_command()
            time.sleep(interval_seconds)
        except Exception as e:
            logger.error(f"Ошибка в периодической отправке времени: {e}")
            time.sleep(interval_seconds)

def main():
    # Запускаем отправку времени в отдельном потоке
    time_thread = threading.Thread(target=send_uptime_periodically, daemon=True)
    time_thread.start()
    
    # Запускаем основной цикл прослушивания WoL пакетов
    run_udp_port_listener_lan(WOL_PORT, INTERFACE_NAME)

# Запуск основного цикла прослушивания
if __name__ == '__main__':
    print(SERVER_MAC_ADDRESS, BROADCAST_IP)

    main()


