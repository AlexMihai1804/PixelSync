import threading
import time

from screenshot import Monitor, mon_number


class MonitorManager:
    def __init__(self, settings_manager, light_manager):
        self.settings_manager = settings_manager
        self.light_manager = light_manager
        self.run = False
        self.threads = []

    def start_sync(self):
        if self.run:
            return  # Already running
            
        self.run = True
        fps = self.settings_manager.fps
        rate = 1 / fps
        for i in range(1, mon_number()):
            t = threading.Thread(target=self.sync_lights, args=(i, rate), daemon=True)
            t.start()
            self.threads.append(t)

    def stop_sync(self):
        if not self.run:
            return  # Already stopped
            
        self.run = False
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.threads = []

    def sync_lights(self, monitor_index, rate):
        def is_light_connected():
            return any(light.get_monitor() == monitor_index and light.enable 
                       and not (light.connection_error and not light.should_retry())
                      for light in self.light_manager.lights)

        try:
            mon = Monitor(monitor_index, self.settings_manager.bar_correction,
                        self.settings_manager.black_bar * self.settings_manager.fps / 2)
                        
            while self.run:
                t_start = time.time()
                if is_light_connected():
                    try:
                        hsv_values = mon.get_mon_hsv()
                        for light in self.light_manager.lights:
                            if light.get_monitor() == monitor_index and light.enable:
                                # Skip lights with persistent connection errors
                                if light.connection_error and not light.should_retry():
                                    continue
                                    
                                # Try to set color, ignore failures
                                try:
                                    # Pass color correction settings from settings_manager
                                    success = light.set_hsv(hsv_values, rate, 
                                                          self.settings_manager.color_correction,
                                                          self.settings_manager.red_gain,
                                                          self.settings_manager.green_gain,
                                                          self.settings_manager.blue_gain,
                                                          self.settings_manager.gamma)
                                    # If light failed, check if it should be considered disconnected
                                    if not success and light.retry_count > light.max_retries:
                                        # Handle light that's become disconnected
                                        self._handle_disconnected_light(light)
                                except Exception as e:
                                    print(f"Error syncing light {light.ip}: {str(e)}")
                                    light.connection_error = True
                                    light.last_error_time = time.time()
                                    light.retry_count += 1
                                    light.start = False
                                    
                                    # If retries exceeded, handle disconnection
                                    if light.retry_count > light.max_retries:
                                        self._handle_disconnected_light(light)
                    except Exception as e:
                        print(f"Error processing screen for monitor {monitor_index}: {str(e)}")
                
                elapsed = time.time() - t_start
                if rate > elapsed:
                    time.sleep(rate - elapsed)
        except Exception as e:
            print(f"Fatal error in monitor thread for monitor {monitor_index}: {str(e)}")
        
        # When stopping, revert lights safely
        try:
            time.sleep(0.25)
            for light in self.light_manager.lights:
                if light.get_monitor() == monitor_index and light.enable:
                    # Only try to revert lights that are likely still connected
                    if not (light.connection_error and not light.should_retry()):
                        try:
                            light.revert_to_initial()
                        except Exception as e:
                            print(f"Error reverting light {light.ip}: {str(e)}")
        except Exception as e:
            print(f"Error during light cleanup for monitor {monitor_index}: {str(e)}")

    def _handle_disconnected_light(self, light):
        """Move a light from connected to disconnected status"""
        # This method would move a light that has persistent connection failures
        # from the active lights list to the disconnected lights list
        for i, connected_light in enumerate(self.light_manager.connected_lights[:]):
            if connected_light[0] == light.ip:
                # Move to disconnected lights
                self.light_manager.disconnected_lights.append(connected_light)
                # Remove from connected lights
                self.light_manager.connected_lights.pop(i)
                # Remove from active lights list
                for j, light_obj in enumerate(self.light_manager.lights[:]):
                    if light_obj.ip == light.ip:
                        self.light_manager.lights.pop(j)
                        break
                break
        
        # Save updated light status
        self.light_manager.save()

