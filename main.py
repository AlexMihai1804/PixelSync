from app import LightControllerApp
from light_manager import LightManager
from monitor_manager import MonitorManager
from settings_manager import SettingsManager


def main():
    settings_manager = SettingsManager()
    light_manager = LightManager(settings_manager)
    monitor_manager = MonitorManager(settings_manager, light_manager)
    app = LightControllerApp(settings_manager, light_manager, monitor_manager)
    app.mainloop()


if __name__ == '__main__':
    main()
