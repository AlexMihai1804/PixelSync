import json

DEFAULT_SETTINGS = {
    "fps": 10,
    "bar_correction": 1,
    "black_bar": 3,
    "lights": []
}


def save(settings: dict) -> None:
    with open("settings.txt", "w") as f:
        json.dump(settings, f)


def load() -> dict:
    settings = DEFAULT_SETTINGS.copy()
    try:
        with open("settings.txt", "r") as f:
            loaded = json.load(f)
        settings.update(loaded)
    except Exception:
        save(settings)
    return settings
