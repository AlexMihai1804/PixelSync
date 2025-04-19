def position_int_to_string(pos: int) -> str:
    positions = {
        0: "WHOLE SCREEN",
        1: "TOP",
        2: "LEFT",
        3: "BOTTOM",
        4: "RIGHT",
        5: "TOP-CENTRE",
        6: "LEFT-CENTRE",
        7: "BOTTOM-CENTRE",
        8: "RIGHT-CENTRE",
        9: "CORNER-TOP-LEFT",
        10: "CORNER-BOTTOM-LEFT",
        11: "CORNER-BOTTOM-RIGHT",
        12: "CORNER-TOP-RIGHT"
    }
    return positions.get(pos, str(pos))


def position_string_to_int(pos: str) -> int:
    mapping = {
        "WHOLE SCREEN": 0,
        "TOP": 1,
        "LEFT": 2,
        "BOTTOM": 3,
        "RIGHT": 4,
        "TOP-CENTRE": 5,
        "LEFT-CENTRE": 6,
        "BOTTOM-CENTRE": 7,
        "RIGHT-CENTRE": 8,
        "CORNER-TOP-LEFT": 9,
        "CORNER-BOTTOM-LEFT": 10,
        "CORNER-BOTTOM-RIGHT": 11,
        "CORNER-TOP-RIGHT": 12
    }
    return mapping.get(pos, 0)


def validate_ip(ip_str: str) -> bool:
    parts = ip_str.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        if not 0 <= int(part) <= 255:
            return False
    return True
