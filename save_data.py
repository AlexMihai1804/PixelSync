import json

settings = {"fps": 10, 'bar_correction': 1,'black_bar':3, 'lights': []}


def save(sett):
    with open("settings.txt", "w") as s:
        json.dump(sett, s)


def load():
    try:
        with open("settings.txt", "r") as s:
            sett = json.load(s)
        settings.update(sett)
    except:
        save(settings)
    return settings
