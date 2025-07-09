import socket
import os
from dotenv import load_dotenv

from network import get_ip_mac_address

load_dotenv()

PORT = os.getenv('PORT')
INTERFACE = os.getenv('INTERFACE')

if PORT is None:
    raise ValueError('PORT environment variable is not set')
PORT = int(PORT)

async def run_udp_port_listener_time(port: int, interface_name: str):
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
    server_socket.bind(('', port))
    print(1)
    # Бесконечный цикл прослушивания
    while True:

        # Получаем данные из сокета
        data, _ = server_socket.recvfrom(1024)
        decoded_packet_data = '-'.join(f'{byte:02x}' for byte in data).upper() + '-'
        print(data)
        return data, decoded_packet_data


if __name__ == '__main__':
    print(INTERFACE)
    import asyncio
    async def main():
        while True:
            data, _ = await run_udp_port_listener_time(PORT, INTERFACE)
            print(data)
    asyncio.run(main())