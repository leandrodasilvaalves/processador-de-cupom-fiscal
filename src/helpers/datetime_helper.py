import datetime

def parse_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")