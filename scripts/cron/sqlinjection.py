def scan_large_log_file_for_sqlinjection(filepath):
    try:
        with (open(filepath, 'r') as file):
            previous_line = None  # To store the previous line
            ip_details = {}  # Dictionary to store IP address details: last occurrence and count
            i = 0
            while True:
                i += 1
                line = file.readline()  # Read the current line
                if not line:  # If no more lines, break the loop
                    break
                line = line.strip()  # Remove any leading/trailing whitespace
                line = line.lower()
                # Check if the previous line meets the criteria
                if previous_line is not None and previous_line.startswith(">>> received url:"):
                    if len(previous_line) > 200 or any(word in previous_line for word in ["and", "or", "select", "union"]):
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
                if details['count'] > 8:
                    print(f"IP {ip}: {details['count']} hits")

    except FileNotFoundError:
        print("File not found. Please check the file path.")
    except Exception as e:
        print(f"An error occurred: {e}")

scan_large_log_file_for_sqlinjection('/var/log/gunicorn/gunicorn-error.log')
