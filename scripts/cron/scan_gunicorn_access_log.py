import re

def count_php_requests(log_file):
    ip_count = {}
    with open(log_file, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) > 6 and (parts[6].endswith('.php') or parts[6].endswith('.xml') or parts[6].startswith('/.well-known')):
                ip_address = parts[0]
                if ip_address in ip_count:
                    ip_count[ip_address] += 1
                else:
                    ip_count[ip_address] = 1
    sorted_ips = sorted(ip_count.items(), key=lambda x: x[1], reverse=True)
    for ip, count in sorted_ips:
        if count > 8:
            print(f"{ip}: {count}")

# Example usage:
count_php_requests('/var/log/gunicorn/gunicorn-access.log')
