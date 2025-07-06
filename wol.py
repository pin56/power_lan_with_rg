import socket

def send_wol(mac_address: str, broadcast_ip: str = "192.168.50.255"):
    # Удаляем разделители из MAC-адреса
    mac_address = mac_address.replace(":", "").replace("-", "").lower()
    if len(mac_address) != 12:
        raise ValueError("Неверный MAC-адрес. Ожидается 12 символов (6 байт).")

    # Создание magic packet
    mac_bytes = bytes.fromhex(mac_address)
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    # Отправка UDP broadcast
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, 9))

    print(f"✅🚀 WOL пакет отправлен на {mac_address.upper()} через {broadcast_ip}")
 

def send_off(mac_address: str, broadcast_ip: str = "192.168.50.255"):
    # 
    mac_address = mac_address.replace(":", "").replace("-", "").lower()
    if len(mac_address) != 12:
        raise ValueError("Неверный MAC-адрес. Ожидается 12 символов (6 байт).")

    # Создание magic packet
    mac_bytes = bytes.fromhex(mac_address)
    # Создаем magic packet для выключения компьютера:
    # - 6 байт 0x00 (магическая последовательность для выключения)
    # - 16 повторений MAC-адреса (96 байт) - аналогично WoL, но с другим магическим числом
    magic_packet = b'\x00' * 6 + mac_bytes * 16

    # Отправка UDP broadcast
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, 9))

    print(f"✅⚫️ OFF пакет отправлен на {mac_address.upper()} через {broadcast_ip}")
 
def send_sleep(mac_address: str, broadcast_ip: str = "192.168.50.255"):
    # 
    mac_address = mac_address.replace(":", "").replace("-", "").lower()
    if len(mac_address) != 12:
        raise ValueError("Неверный MAC-адрес. Ожидается 12 символов (6 байт).")

    # Создание magic packet
    mac_bytes = bytes.fromhex(mac_address)
    # Создаем magic packet для выключения компьютера:
    # - 6 байт 0x99 (магическая последовательность для сна)
    # - 16 повторений MAC-адреса (96 байт) - аналогично WoL, но с другим магическим числом
    magic_packet = b'\x99' * 6 + mac_bytes * 16

    # Отправка UDP broadcast
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, 9))

    print(f"✅🛏️ Sleep пакет отправлен на {mac_address.upper()} через {broadcast_ip}")
 


if __name__ == "__main__":
    while True:
        print('Выберите пункт меню:')
        print('1. Включение ПК')
        print('2. Перевод в сон')
        print('3. Выключение ПК')
        while True:
            inp = int(input())
            if inp == 1:
                send_wol('00:D8:61:33:5E:65', "192.168.50.255")
            elif inp == 2:
                send_sleep('00:D8:61:33:5E:65', "192.168.50.255")
            elif inp == 3:
                send_off('00:D8:61:33:5E:65', "192.168.50.255")
            else: 
                break