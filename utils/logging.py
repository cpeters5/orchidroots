# utils/logging.py
import logging

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'request') and record.request:
            record.ip_address = record.request.ip_address if hasattr(record.request, 'ip_address') else 'unknown'
        else:
            record.ip_address = 'unknown'
        return super().format(record)