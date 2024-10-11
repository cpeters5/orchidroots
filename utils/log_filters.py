import logging

class IPAddressFilter(logging.Filter):
    def filter(self, record):
        # Attach a default IP address if not set (helps avoid errors for non-request logs)
        if not hasattr(record, 'ip'):
            record.ip = 'unknown'
        return True
