#  Scan gunicorn access log file to look for malicious requests.
# Run with either 'ip' or 'path' parameter for ip count or ip+path count

import sys

def scan_for_unauthorized_access(log_file):
    exact_paths = {'/'}
    allowed_prefixes  = {'/', '/search', '/common', '/detail', '/login', '/display', '/animalia', '/aves', '/fungi',
                         '/other', '/orchidaceae', '/accounts', '/documents', '/gallery', '/donation' }
    access_count = {}
    ip_count = {}
    if len(sys.argv) > 1:
        param = sys.argv[1]
    else:
        exit()

    with open(log_file, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) > 6:
                ip_address = parts[0]
                method = parts[5].strip('"')  # HTTP method, stripping leading quotes
                path = parts[6].split('?')[0]  # Removing any query parameters

                # Ensure the method is a valid HTTP method to avoid parsing errors
                if method in {'GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH'}:
                    # Check path against exact and prefix paths
                    if not (path in exact_paths or any(path.startswith(prefix + '/') or path == prefix for prefix in allowed_prefixes)):
                        if param == 'path':
                            key = (ip_address, path)
                            if key in access_count:
                                access_count[key] += 1
                            else:
                                access_count[key] = 1
                        elif param == 'ip':
                            ip_key = ip_address
                            if ip_key in ip_count:
                                ip_count[ip_key] += 1
                            else:
                                ip_count[ip_key] = 1

    if param == 'path':
        # Sorting by IP and then by count
        for key, count in sorted(access_count.items(), key=lambda x: (x[1], x[0][0]), reverse=True):
            if count > 8:
                print(f"IP Address: {key[0]}, Path: {key[1]}, Count: {count}")

    elif param == 'ip':
        for key, count in sorted(ip_count.items(), key=lambda x: (x[1]), reverse=True):
            if count > 8:
                print(f"IP Address: {key}, Count: {count}")


scan_for_unauthorized_access('/var/log/gunicorn/gunicorn-access.log')
