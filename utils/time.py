def format_time_left(seconds: float) -> str:
    days = int(seconds // (24 * 3600))
    seconds %= (24 * 3600)
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)

    time_str = ""
    if days > 0:
        time_str += f"{days} дн.\n"
    if hours > 0:
        time_str += f"{hours} ч.\n"
    if minutes > 0:
        time_str += f"{minutes} мин."

    return time_str.strip()
