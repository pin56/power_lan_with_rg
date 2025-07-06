
import psutil


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