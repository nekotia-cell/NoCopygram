def format_balance(balance: int) -> str:
    return "{:,}".format(balance).replace(",", ".")
