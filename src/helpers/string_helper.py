def extract_numbers(value: str) -> str:
    return ''.join(filter(str.isdigit, value))