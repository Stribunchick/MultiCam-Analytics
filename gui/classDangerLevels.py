LEVEL_OPTIONS = [
    ("safe", "Безопасный", "#16a34a"),
    ("attention", "Внимание", "#f59e0b"),
    ("danger", "Опасный", "#dc2626"),
    ("critical", "Критический", "#7f1d1d"),
]

DEFAULT_LEVEL = LEVEL_OPTIONS[0][0]

_LEVEL_MAP = {
    key: {
        "label": label,
        "color": color,
    }
    for key, label, color in LEVEL_OPTIONS
}


def normalize_level(level):
    if level in _LEVEL_MAP:
        return level
    return DEFAULT_LEVEL


def level_label(level):
    return _LEVEL_MAP[normalize_level(level)]["label"]


def level_color(level):
    return _LEVEL_MAP[normalize_level(level)]["color"]


def level_bgr(level):
    color = level_color(level).lstrip("#")
    if len(color) != 6:
        return (0, 255, 0)

    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return (blue, green, red)
