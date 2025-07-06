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

    print(f"✅ WOL пакет отправлен на {mac_address.upper()} через {broadcast_ip}")
 
# Запуск
if __name__ == "__main__":
    send_wol("00:D8:61:33:5E:65", "192.168.50.255")
