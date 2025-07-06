import psutil
import socket

def list_network_interfaces():
    """
    Выводит список всех доступных сетевых интерфейсов с их IP и MAC адресами
    """
    print("=== Доступные сетевые интерфейсы ===\n")
    
    # Получаем все сетевые интерфейсы
    interfaces = psutil.net_if_addrs()
    
    for interface_name, addresses in interfaces.items():
        print(f"Интерфейс: {interface_name}")
        
        ip_addresses = []
        mac_addresses = []
        
        for addr in addresses:
            if addr.family == socket.AF_INET:  # IPv4
                ip = addr.address
                if ip != '127.0.0.1':  # Исключаем localhost
                    ip_addresses.append(ip)
            elif addr.family == psutil.AF_LINK:  # MAC адрес
                mac = addr.address
                if mac and mac != '00:00:00:00:00:00':
                    mac_addresses.append(mac)
        
        if ip_addresses:
            print(f"  IP адреса: {', '.join(ip_addresses)}")
        if mac_addresses:
            print(f"  MAC адреса: {', '.join(mac_addresses)}")
        
        print("-" * 50)

if __name__ == "__main__":
    list_network_interfaces() 