from datetime import datetime


def log_message(msg: str):
    formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{formatted_time} - {msg}")


