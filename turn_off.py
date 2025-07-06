# Скрипт для выключения компьютера при получении Wake-on-LAN пакета
# Слушает UDP порт 9 и при получении правильного WoL пакета выключает систему

import socket
import os
import logging
import psutil

# Константы
WOL_PORT = 9  # Стандартный порт для Wake-on-LAN
INTERFACE_NAME = 'Ethernet 4'  # Имя сетевого интерфейса для мониторинга

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


def assemble_wol_packet(mac_address: str) -> str:
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
    return f'{"FF-" * 6}{(mac_address + "-") * 16}'


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


def run_udp_port_listener(port: int, interface_name: str):
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
    assembled_wol_packet = assemble_wol_packet(mac_addr)

    # Бесконечный цикл прослушивания
    while True:
        # Получаем данные из сокета
        data, _ = server_socket.recvfrom(1024)

        # Проверяем, является ли пакет WoL пакетом
        is_wol_packet = check_is_wol_packet(data, assembled_wol_packet)

        # Если это WoL пакет - выключаем компьютер
        if is_wol_packet == 1:
            if os.name == 'posix':  # Linux/Unix системы
                os.system('sudo shutdown -h now')
            elif os.name == 'nt':   # Windows системы
                os.system('shutdown -s -t 0 -f')


# Запуск основного цикла прослушивания
run_udp_port_listener(WOL_PORT, INTERFACE_NAME)