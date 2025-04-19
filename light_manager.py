from light import Light, light_online


class LightManager:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.lights = []
        self.connected_lights = []
        self.disconnected_lights = []
        
        # Initialize lights from settings
        self._load_lights_from_settings()
    
    def _load_lights_from_settings(self):
        # Load saved lights from settings
        for light_data in self.settings_manager.settings.get("lights", []):
            try:
                ip = light_data[0]
                props = light_data[1:]
                if light_online(ip):
                    light_obj = Light(ip)
                    light_obj.set_prop(props)
                    self.lights.append(light_obj)
                    self.connected_lights.append(light_data)
                else:
                    self.disconnected_lights.append(light_data)
            except Exception as e:
                print(f"Error loading light {light_data[0] if light_data else 'unknown'}: {str(e)}")
                # Skip lights that fail to load
                if light_data:
                    self.disconnected_lights.append(light_data)
    
    def lights_status(self):
        """Return tuple of (total, connected, active, deactivated, disconnected) light counts"""
        total = len(self.connected_lights) + len(self.disconnected_lights)
        connected = len(self.connected_lights)
        active = sum(1 for light in self.connected_lights if light[6])  # light[6] is enable status
        deactivated = connected - active
        disconnected = len(self.disconnected_lights)
        return total, connected, active, deactivated, disconnected

    def refresh(self):
        # Create copies to avoid modifying lists during iteration
        disconnected_copy = self.disconnected_lights.copy()
        
        # Check connected lights that may have disconnected - this is now handled by monitor_manager
        # when failures occur during operation
        
        # Check disconnected lights that may have reconnected
        for i, item in enumerate(disconnected_copy):
            try:
                if light_online(item[0]):
                    props = item[1:]
                    light_obj = Light(item[0])
                    light_obj.set_prop(props)
                    self.lights.append(light_obj)
                    self.connected_lights.append(item)
                    
                    # Remove from disconnected list
                    for j, disconnected in enumerate(self.disconnected_lights):
                        if disconnected[0] == item[0]:
                            self.disconnected_lights.pop(j)
                            break
            except Exception as e:
                print(f"Error reconnecting to light {item[0]}: {str(e)}")
    
    def add_light(self, light_data):
        """Add a new light to the manager"""
        ip = light_data[0]
        
        # First check if this IP already exists
        for i, light in enumerate(self.connected_lights):
            if light[0] == ip:
                # Update existing connected light
                self.connected_lights[i] = light_data
                # Update light object
                for light_obj in self.lights:
                    if light_obj.ip == ip:
                        light_obj.set_prop(light_data[1:])
                return
        
        for i, light in enumerate(self.disconnected_lights):
            if light[0] == ip:
                # Move from disconnected to connected
                self.disconnected_lights.pop(i)
                self.connected_lights.append(light_data)
                # Create new light object
                try:
                    light_obj = Light(ip)
                    light_obj.set_prop(light_data[1:])
                    self.lights.append(light_obj)
                except Exception as e:
                    print(f"Error creating light object for {ip}: {str(e)}")
                    # If creation fails, put back in disconnected
                    self.connected_lights.pop(-1)
                    self.disconnected_lights.append(light_data)
                return
        
        # If not existing, add as new
        try:
            # Check if online first
            if light_online(ip):
                light_obj = Light(ip)
                light_obj.set_prop(light_data[1:])
                self.lights.append(light_obj)
                self.connected_lights.append(light_data)
            else:
                self.disconnected_lights.append(light_data)
        except Exception as e:
            print(f"Error adding new light {ip}: {str(e)}")
            self.disconnected_lights.append(light_data)
    
    def save(self):
        """Save all lights configuration to settings"""
        all_lights = self.connected_lights + self.disconnected_lights
        self.settings_manager.save(all_lights)

