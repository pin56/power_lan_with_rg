from pc import run_udp_port_listener_time

while True:
    data, _ = run_udp_port_listener_time(59681, 'en0')
    print(data)