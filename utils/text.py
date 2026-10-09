def gram_declension(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return "Кото-грамм"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return "Кото-грамма"
    else:
        return "Кото-грамм"


def time_declension(count: int, word: str) -> str:
    if word == "час":
        if count % 10 == 1 and count % 100 != 11:
            return "час"
        elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
            return "часа"
        else:
            return "часов"
    elif word == "минут":
        if count % 10 == 1 and count % 100 != 11:
            return "минута"
        elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
            return "минуты"
        else:
            return "минут"
    return ""
