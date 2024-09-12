import re
import sys
from collections import Counter


# Function to extract IPs starting with a specified pattern
def extract_ip_addresses(log_file_path, ip_prefix):
    ip_pattern = re.compile(rf'^{re.escape(ip_prefix)}\.\d+\.\d+')
    ip_addresses = []

    with open(log_file_path, 'r') as file:
        for line in file:
            match = ip_pattern.match(line)
            if match:
                ip = match.group(0)
                ip_addresses.append(ip)

    return ip_addresses


# Function to count IP occurrences and sort them by frequency
def count_ip_occurrences(log_file_path, ip_prefix):
    ip_addresses = extract_ip_addresses(log_file_path, ip_prefix)
    ip_count = Counter(ip_addresses)

    # Sort by occurrences in descending order
    sorted_ip_count = ip_count.most_common()

    return sorted_ip_count


# Function to print the sorted result
def print_sorted_ip_count(log_file_path, ip_prefix):
    sorted_ip_count = count_ip_occurrences(log_file_path, ip_prefix)

    print(f"{'IP Address':<20}{'Occurrences'}")
    print("=" * 30)
    for ip, count in sorted_ip_count:
        print(f"{ip:<20}{count}")


# Main function to handle command line arguments
def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_file_path> <ip_prefix>")
        sys.exit(1)

    log_file_path = '/var/log/gunicorn/gunicorn-access.log'
    ip_prefix = sys.argv[1]

    print_sorted_ip_count(log_file_path, ip_prefix)


# Example usage: call main function
if __name__ == "__main__":
    main()

