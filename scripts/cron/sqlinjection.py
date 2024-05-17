def scan_large_log_file_track_last_occurrence(filepath):
    try:
        with open(filepath, 'r') as file:
            previous_line = None  # To store the previous line
            ip_details = {}  # Dictionary to store IP address details: last occurrence and count

            while True:
                line = file.readline()  # Read the current line
                if not line:  # If no more lines, break the loop
                    break
                line = line.strip()  # Remove any leading/trailing whitespace

                # Check if the previous line meets the criteria
                if previous_line is not None and previous_line.startswith(">>> Received URL:") and len(previous_line) > 200:
                    # Extract the last word from the current line, presumed to be the IP address
                    last_word = line.split()[-1]
                    # Update the IP address details in the dictionary
                    if last_word in ip_details:
                        ip_details[last_word]['count'] += 1
                        ip_details[last_word]['last_occurrence'] = (previous_line, line)
                    else:
                        ip_details[last_word] = {'count': 1, 'last_occurrence': (previous_line, line)}

                # Update the previous line to current for the next iteration
                previous_line = line

            # After finishing reading the file, print the details for each IP
            for ip, details in ip_details.items():
                long_url_line, following_line = details['last_occurrence']
                print(f"IP {ip}: {details['count']} hits")

    except FileNotFoundError:
        print("File not found. Please check the file path.")
    except Exception as e:
        print(f"An error occurred: {e}")

scan_large_log_file_track_last_occurrence('/var/log/gunicorn/gunicorn-error.log')
