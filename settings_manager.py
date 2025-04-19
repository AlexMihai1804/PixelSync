from save_data import load, save


class SettingsManager:
    def __init__(self):
        self.settings = load()
        self.fps = self.settings.get("fps", 10)
        self.bar_correction = self.settings.get("bar_correction", 1)
        self.black_bar = self.settings.get("black_bar", 3)
        
        # Color correction settings
        self.color_correction = self.settings.get("color_correction", False)
        self.red_gain = self.settings.get("red_gain", 100)
        self.green_gain = self.settings.get("green_gain", 100)
        self.blue_gain = self.settings.get("blue_gain", 100)
        self.gamma = self.settings.get("gamma", 100)  # 100 means gamma 1.0

    def save(self, lights_data):
        self.settings["fps"] = self.fps
        self.settings["bar_correction"] = self.bar_correction
        self.settings["black_bar"] = self.black_bar
        self.settings["lights"] = lights_data
        
        # Save color correction settings
        self.settings["color_correction"] = self.color_correction
        self.settings["red_gain"] = self.red_gain
        self.settings["green_gain"] = self.green_gain
        self.settings["blue_gain"] = self.blue_gain
        self.settings["gamma"] = self.gamma
        
        save(self.settings)
