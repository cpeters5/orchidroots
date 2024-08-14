import re
from collections import defaultdict
from datetime import datetime


def parse_log_file(file_path):
    ip_pattern = r'(\d+\.\d+)\.\d+\.\d+'
    date_pattern = r'\[(\d{2}/\w{3}/\d{4}):(\d{2}:\d{2}:\d{2})'
    request_pattern = r'"([^"]*)"'
    status_pattern = r'" (\d{3}) '
    user_agent_pattern = r'"([^"]*)"$'
    bot_patterns = {
        'Bytespider': r'Bytespider',
        'Googlebot': r'Googlebot',              # good bot
        'Bingbot': r'bingbot',                  # Googbot
        'Yandexbot': r'Yandexbot',
        'Baiduspider': r'Baiduspider',
        'GPTBot': r'GPTBot/\d+\.\d+',
        'AhrefsBot': r'AhrefsBot/\d+\.\d+',     # good bot
        'DataForSeoBot': r'DataForSeoBot/\d+\.\d+',
        'SemrushBot': r'SemrushBot/\d+',        # good bot
        'ChatGLM': r' ChatGLM-Spider/\d+\.\d+', #bad
    }

    ip_block_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    gptbot_details = defaultdict(list)

    with open(file_path, 'r') as file:
        for line in file:
            ip_match = re.search(ip_pattern, line)
            date_match = re.search(date_pattern, line)
            request_match = re.search(request_pattern, line)
            status_match = re.search(status_pattern, line)
            user_agent_match = re.search(user_agent_pattern, line)

            if all([ip_match, date_match, request_match, status_match, user_agent_match]):
                ip_block = ip_match.group(1)
                date = date_match.group(1)
                time = date_match.group(2)
                full_date = f"{date} {time}"
                request = request_match.group(1)
                status = status_match.group(1)
                user_agent = user_agent_match.group(1)

                date = datetime.strptime(date, '%d/%b/%Y').strftime('%Y-%m-%d')

                bot_name = 'Unknown'
                for name, pattern in bot_patterns.items():
                    if re.search(pattern, user_agent, re.IGNORECASE):
                        bot_name = name
                        break

                ip_block_counts[date][ip_block][bot_name] += 1

                if bot_name == 'GPTBot':
                    gptbot_details[date].append({
                        'ip': ip_match.group(0),
                        'time': time,
                        'request': request,
                        'status': status,
                        'user_agent': user_agent
                    })

    return ip_block_counts, gptbot_details


def xwrite_to_log(ip_block_counts, gptbot_details, output_file):
    with open(output_file, 'w') as file:
        for date, blocks in sorted(ip_block_counts.items()):
            file.write(f"Date: {date}\n")
            for block, bots in sorted(blocks.items(), key=lambda x: sum(x[1].values()), reverse=True):
                total_count = sum(bots.values())
                file.write(f"  IP Block: {block}.*.*, Total Count: {total_count}\n")
                for bot, count in sorted(bots.items(), key=lambda x: x[1], reverse=True):
                    file.write(f"    Bot: {bot}, Count: {count}\n")

            if date in gptbot_details:
                file.write("\n  GPTBot Details:\n")
                for entry in gptbot_details[date]:
                    file.write(f"    Time: {entry['time']}, IP: {entry['ip']}\n")
                    file.write(f"    Request: {entry['request']}\n")
                    file.write(f"    Status: {entry['status']}\n")
                    file.write(f"    User-Agent: {entry['user_agent']}\n\n")

            file.write("\n")


def write_to_log(ip_block_counts, gptbot_details, output_file):
    with open(output_file, 'w') as file:
        for date, blocks in sorted(ip_block_counts.items()):
            file.write(f"Date: {date}\n")
            significant_activity = False
            for block, bots in sorted(blocks.items(), key=lambda x: sum(x[1].values()), reverse=True):
                total_count = sum(bots.values())
                if total_count >= 200:
                    significant_activity = True
                    file.write(f"{block}.*.*\t{total_count}")
                    for bot, count in sorted(bots.items(), key=lambda x: x[1], reverse=True):
                        file.write(f"\t{bot}\t{count}")
                    file.write("\n")

            # if date in gptbot_details:
            #     file.write("\n  GPTBot Details:\n")
            #     for entry in gptbot_details[date]:
            #         file.write(f"    Time: {entry['time']}, IP: {entry['ip']}\n")
            #         file.write(f"    Request: {entry['request']}\n")
            #         file.write(f"    Status: {entry['status']}\n")
            #         file.write(f"    User-Agent: {entry['user_agent']}\n")
            #         if 'abuse_score' in entry and entry['abuse_score'] is not None:
            #             file.write(f"    AbuseIPDB Score: {entry['abuse_score']}\n")
            #         file.write("\n")

            if significant_activity:
                file.write("\n")
            else:
                file.write("No significant crawler activity (>= 200 requests) for this date.\n\n")


def main():
    input_log = '/var/log/gunicorn/gunicorn-access.log'
    output_log = '/var/log/bluenanta/badbot.log'

    ip_block_counts, gptbot_details = parse_log_file(input_log)
    write_to_log(ip_block_counts, gptbot_details, output_log)
    print(f"Analysis complete. Results written to {output_log}")


if __name__ == "__main__":
    main()