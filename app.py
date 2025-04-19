import threading
import time
import tkinter as tk

import customtkinter
from customtkinter import CTk, CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkSlider, CTkComboBox, CTkCheckBox, CTkFont

from screenshot import mon_number
from utils import position_int_to_string, position_string_to_int, validate_ip


class LightControllerApp(CTk):
    def __init__(self, settings_manager, light_manager, monitor_manager):
        super().__init__()
        customtkinter.set_default_color_theme("dark-blue")
        self.title("Light Controller")
        self.geometry("1000x600")
        self.settings_manager = settings_manager
        self.light_manager = light_manager
        self.monitor_manager = monitor_manager

        # Status variables
        self.total_lights_text = tk.StringVar(value="Loaded lights:")
        self.connected_label_text = tk.StringVar(value="Connected lights:")
        self.active_label_text = tk.StringVar(value="Active lights:")
        self.deactivated_label_text = tk.StringVar(value="Deactivated lights:")
        self.disconnected_label_text = tk.StringVar(value="Disconnected lights:")

        self.run = False
        self._build_frames()
        self.select_frame(self.status_frame)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        threading.Thread(target=self._update_lights_state, daemon=True).start()

    def _build_frames(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        # Create frames
        self.main_menu_frame = CTkFrame(self)
        self.config_buttons_frame = CTkFrame(self)
        self.status_frame = CTkFrame(self)
        self.add_new_light_frame = CTkFrame(self)
        self.add_new_light_manual_frame = CTkFrame(self)
        self.edit_lights_frame = CTkFrame(self)
        self.edit_settings_frame = CTkFrame(self)

        self._create_main_menu_frame()
        self._create_config_buttons_frame()
        self._create_status_frame()
        self._create_add_new_light_frame()
        self._create_add_new_light_manual_frame()
        self._create_edit_lights_frame()
        self._create_edit_settings_frame()

        # Place frames in grid
        self.main_menu_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.config_buttons_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        for frame in [self.status_frame, self.add_new_light_frame, self.add_new_light_manual_frame,
                      self.edit_lights_frame, self.edit_settings_frame]:
            frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=8, pady=8)

    def _create_main_menu_frame(self):
        run_btn_text = tk.StringVar(value="Start")
        CTkButton(self.main_menu_frame, textvariable=run_btn_text,
                  command=lambda: self._toggle_run(run_btn_text)).pack(padx=16, pady=8, fill="both")
        for txt in [self.total_lights_text, self.connected_label_text, self.active_label_text,
                    self.deactivated_label_text, self.disconnected_label_text]:
            CTkLabel(self.main_menu_frame, textvariable=txt).pack(fill="x")
        CTkButton(self.main_menu_frame, text="Refresh lights", command=self._update_lights_text).pack(padx=16, pady=8,
                                                                                                      fill="both")
        CTkButton(self.main_menu_frame, text="Exit", command=self.close_app).pack(padx=16, pady=8, fill="both")

    def _create_config_buttons_frame(self):
        CTkButton(self.config_buttons_frame, text="Status page",
                  command=lambda: self.select_frame(self.status_frame)).pack(padx=16, pady=8, fill="x")
        CTkButton(self.config_buttons_frame, text="New Light (Auto)",
                  command=lambda: [self.select_frame(self.add_new_light_frame), self.auto_discover()]).pack(padx=16,
                                                                                                            pady=8,
                                                                                                            fill="x")
        CTkButton(self.config_buttons_frame, text="New Light (Manual)",
                  command=lambda: self.select_frame(self.add_new_light_manual_frame)).pack(padx=16, pady=8, fill="x")
        CTkButton(self.config_buttons_frame, text="Edit Lights",
                  command=lambda: self.select_frame(self.edit_lights_frame)).pack(padx=16, pady=8, fill="x")
        CTkButton(self.config_buttons_frame, text="Settings",
                  command=lambda: self.select_frame(self.edit_settings_frame)).pack(padx=16, pady=8, fill="x")

    def _create_status_frame(self):
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=1)

        # Title
        CTkLabel(self.status_frame, text="System Status", font=(CTkFont, 26)).grid(row=0, column=0, columnspan=2, pady=15)

        # Create frames for different sections
        monitor_status_frame = CTkFrame(self.status_frame)
        monitor_status_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        settings_status_frame = CTkFrame(self.status_frame)
        settings_status_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        actions_frame = CTkFrame(self.status_frame)
        actions_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        # Initialize status StringVars
        self.status_total_lights = tk.StringVar(value="Total lights: 0")
        self.status_connected_lights = tk.StringVar(value="Connected lights: 0")
        self.status_active_lights = tk.StringVar(value="Active lights: 0")
        self.status_deactivated_lights = tk.StringVar(value="Deactivated lights: 0")
        self.status_disconnected_lights = tk.StringVar(value="Disconnected lights: 0")

        # Monitor Status Section
        CTkLabel(monitor_status_frame, text="Monitor Information", font=(CTkFont, 20)).pack(pady=5)

        # Real monitor count is one less than reported by mss
        actual_monitor_count = mon_number() - 1
        self.status_monitor_count = tk.StringVar(value=f"Detected monitors: {actual_monitor_count}")
        CTkLabel(monitor_status_frame, textvariable=self.status_monitor_count).pack(anchor="w", padx=10, pady=2)

        # Create a frame for monitor details
        monitors_details_frame = CTkFrame(monitor_status_frame)
        monitors_details_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Fill monitor details with more information
        import mss
        sct = mss.mss()
        for i in range(1, mon_number()):
            mon_info = sct.monitors[i]
            width = mon_info["width"]
            height = mon_info["height"]

            # Count lights assigned to this monitor
            assigned_lights = sum(1 for light in self.light_manager.connected_lights if light[1] == i)

            monitor_frame = CTkFrame(monitors_details_frame)
            monitor_frame.pack(fill="x", padx=10, pady=5)

            CTkLabel(monitor_frame, text=f"Monitor {i}", font=(CTkFont, 16)).pack(anchor="w", pady=(5,0))
            CTkLabel(monitor_frame, text=f"Resolution: {width}x{height}").pack(anchor="w", padx=10)
            CTkLabel(monitor_frame, text=f"Assigned lights: {assigned_lights}").pack(anchor="w", padx=10)

        # Settings Status Section
        CTkLabel(settings_status_frame, text="Current Settings", font=(CTkFont, 20)).pack(pady=5)

        self.status_fps = tk.StringVar(value=f"FPS: {self.settings_manager.fps}")
        self.status_bar_correction = tk.StringVar(
            value=f"Bar correction: {'Enabled' if self.settings_manager.bar_correction else 'Disabled'}")
        self.status_black_bar = tk.StringVar(value=f"Black bar value: {self.settings_manager.black_bar}")

        for txt in [self.status_fps, self.status_bar_correction, self.status_black_bar]:
            CTkLabel(settings_status_frame, textvariable=txt).pack(anchor="w", padx=10, pady=2)

        # Connected Lights List
        CTkLabel(settings_status_frame, text="Connected Lights:", font=(CTkFont, 16)).pack(anchor="w", padx=10, pady=(10, 2))
        self.status_lights_list = tk.Listbox(settings_status_frame, height=5, background="grey10",
                                             fg="#DCE4EE", borderwidth=0, highlightthickness=0)
        self.status_lights_list.pack(fill="both", expand=True, padx=10, pady=5)

        # Actions Section
        CTkLabel(actions_frame, text="Actions", font=(CTkFont, 20)).pack(pady=5)

        CTkButton(actions_frame, text="Refresh Status",
                  command=self._refresh_status_page, font=(CTkFont, 16)).pack(pady=10, fill="x", padx=20)

        CTkButton(actions_frame, text="Test All Lights",
                  command=self._test_all_lights, font=(CTkFont, 16)).pack(pady=10, fill="x", padx=20)

        # Initial status update
        self._refresh_status_page()

    def _refresh_status_page(self):
        # Update light status
        total, connected, active, deactivated, disconnected = self.light_manager.lights_status()
        self.status_total_lights.set(f"Total lights: {total}")
        self.status_connected_lights.set(f"Connected lights: {connected}")
        self.status_active_lights.set(f"Active lights: {active}")
        self.status_deactivated_lights.set(f"Deactivated lights: {deactivated}")
        self.status_disconnected_lights.set(f"Disconnected lights: {disconnected}")

        # Update connected lights list
        self.status_lights_list.delete(0, tk.END)
        for light in self.light_manager.connected_lights:
            status = "Active" if light[6] else "Deactivated"
            self.status_lights_list.insert(tk.END, f"{light[5]} ({light[0]}) - {status}")

        # Update monitor information with correct count
        actual_monitor_count = mon_number() - 1
        self.status_monitor_count.set(f"Detected monitors: {actual_monitor_count}")

        # Update settings information
        self.status_fps.set(f"FPS: {self.settings_manager.fps}")
        self.status_bar_correction.set(
            f"Bar correction: {'Enabled' if self.settings_manager.bar_correction else 'Disabled'}")
        self.status_black_bar.set(f"Black bar value: {self.settings_manager.black_bar}")

    def _test_all_lights(self):
        # Test all connected lights by identifying them in sequence
        threading.Thread(target=self._identify_all_lights, daemon=True).start()

    def _identify_all_lights(self):
        for light in self.light_manager.lights:
            if light.enable:
                light.identify()
                time.sleep(0.5)  # Small delay between lights

    def _create_add_new_light_frame(self):
        self.add_new_light_frame.grid_columnconfigure(0, weight=1)
        self.add_new_light_frame.grid_columnconfigure(1, weight=1)
        self.add_new_light_frame.grid_columnconfigure(2, weight=1)
        CTkLabel(self.add_new_light_frame, text="New Light (Auto)", font=(CTkFont, 26)).grid(column=0, row=0,
                                                                                             columnspan=3, pady=15)
        self.discovered_list = tk.Listbox(self.add_new_light_frame, selectbackground="#1f538d", fg="#DCE4EE",
                                          height=6, background="grey10", borderwidth=0, highlightthickness=0,
                                          selectforeground="#DCE4EE", activestyle="none", font=(CTkFont, 12))
        self.discovered_list.grid(column=0, row=1, rowspan=3, padx=8, pady=8, sticky="ew")
        CTkButton(self.add_new_light_frame, text="Identify selected", font=(CTkFont, 20),
                  command=lambda: self.identify(self.discovered_list.curselection())).grid(row=1, column=2, sticky="w")
        CTkButton(self.add_new_light_frame, text="Refresh", command=self.auto_discover, font=(CTkFont, 20)
                  ).grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        self.entry_name = CTkEntry(self.add_new_light_frame, placeholder_text="Light name", font=(CTkFont, 12))
        self.entry_name.grid(column=1, row=3, columnspan=2, sticky="ew", padx=5, pady=5)

        # Add saturation slider
        self.sat_label_auto = CTkLabel(self.add_new_light_frame, text="Saturation:100", font=(CTkFont, 20))
        self.sat_label_auto.grid(column=0, row=5, padx=5, pady=5)
        self.sat_val_auto = customtkinter.IntVar()
        self.sat_slider_auto = CTkSlider(self.add_new_light_frame, from_=0, to=200, number_of_steps=20,
                                     variable=self.sat_val_auto,
                                     command=lambda x: self.update_label_sat(x, self.sat_label_auto))
        self.sat_slider_auto.set(100)
        self.sat_slider_auto.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        # Add brightness slider
        self.bri_label_auto = CTkLabel(self.add_new_light_frame, text="Brightness:100", font=(CTkFont, 20))
        self.bri_label_auto.grid(column=0, row=6, padx=5, pady=5)
        self.bri_val_auto = customtkinter.IntVar()
        self.bri_slider_auto = CTkSlider(self.add_new_light_frame, from_=0, to=200, number_of_steps=20,
                                     variable=self.bri_val_auto,
                                     command=lambda x: self.update_label_bri(x, self.bri_label_auto))
        self.bri_slider_auto.set(100)
        self.bri_slider_auto.grid(row=6, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        # Add position selector
        CTkLabel(self.add_new_light_frame, text="Select position", font=(CTkFont, 20)).grid(column=0, row=7, padx=5, pady=5)
        self.position_select_var_auto = customtkinter.StringVar(value="WHOLE SCREEN")
        self.position_select_auto = CTkComboBox(self.add_new_light_frame, state="readonly",
                                            values=["WHOLE SCREEN", "TOP", "LEFT", "BOTTOM", "RIGHT",
                                                    "TOP-CENTRE", "LEFT-CENTRE", "BOTTOM-CENTRE",
                                                    "RIGHT-CENTRE", "CORNER-TOP-LEFT", "CORNER-BOTTOM-LEFT",
                                                    "CORNER-BOTTOM-RIGHT", "CORNER-TOP-RIGHT"],
                                            variable=self.position_select_var_auto)
        self.position_select_auto.grid(column=1, row=7, columnspan=2, sticky="ew", padx=5, pady=5)

        # Add monitor selector
        CTkLabel(self.add_new_light_frame, text="Select monitor", font=(CTkFont, 20)).grid(column=0, row=8, padx=5, pady=5)
        self.monitor_select_var_auto = customtkinter.StringVar(value="1")
        self.monitor_select_auto = CTkComboBox(self.add_new_light_frame, state="readonly",
                                           values=[str(m + 1) for m in range(mon_number() - 1)],
                                           variable=self.monitor_select_var_auto)
        self.monitor_select_auto.grid(column=1, row=8, columnspan=2, sticky="ew", padx=5, pady=5)

        # Add enable checkbox
        self.enable_check_var_auto = customtkinter.IntVar()
        self.enable_check_var_auto.set(1)
        self.check_enable_auto = CTkCheckBox(self.add_new_light_frame, text="Enable light",
                                         variable=self.enable_check_var_auto, onvalue=1, offvalue=0,
                                         font=(CTkFont, 20))
        self.check_enable_auto.grid(column=0, row=9, padx=5, pady=5)

        # Add and Back buttons
        CTkButton(self.add_new_light_frame, text="Add Light", command=self.add_light_auto, font=(CTkFont, 20)
                  ).grid(column=1, row=10, pady=20)
        CTkButton(self.add_new_light_frame, text="Back", command=lambda: self.select_frame(self.status_frame),
                  font=(CTkFont, 20)
                  ).grid(column=0, row=10, pady=20)

    def _create_add_new_light_manual_frame(self):
        self.add_new_light_manual_frame.grid_columnconfigure(0, weight=1)
        self.add_new_light_manual_frame.grid_columnconfigure(1, weight=2)
        CTkLabel(self.add_new_light_manual_frame, text="New Light (Manual)", font=(CTkFont, 26)).grid(column=0, row=0,
                                                                                                      columnspan=2,
                                                                                                      pady=15)
        CTkLabel(self.add_new_light_manual_frame, text="Light IP", font=(CTkFont, 20)).grid(column=0, row=1, padx=10,
                                                                                            pady=10)
        self.entry_ip_manual = CTkEntry(self.add_new_light_manual_frame, placeholder_text="192.168.xxx.xxx",
                                        font=(CTkFont, 12))
        self.entry_ip_manual.grid(column=1, row=1, sticky="ew", padx=10, pady=10)
        CTkLabel(self.add_new_light_manual_frame, text="Light Name", font=(CTkFont, 20)).grid(column=0, row=2, padx=10,
                                                                                              pady=10)
        self.entry_name_manual = CTkEntry(self.add_new_light_manual_frame, placeholder_text="Light name",
                                          font=(CTkFont, 12))
        self.entry_name_manual.grid(column=1, row=2, sticky="ew", padx=10, pady=10)

        # Add saturation slider
        self.sat_label_manual = CTkLabel(self.add_new_light_manual_frame, text="Saturation:100", font=(CTkFont, 20))
        self.sat_label_manual.grid(column=0, row=3, padx=10, pady=10)
        self.sat_val_manual = customtkinter.IntVar()
        self.sat_slider_manual = CTkSlider(self.add_new_light_manual_frame, from_=0, to=200, number_of_steps=20,
                                       variable=self.sat_val_manual,
                                       command=lambda x: self.update_label_sat(x, self.sat_label_manual))
        self.sat_slider_manual.set(100)
        self.sat_slider_manual.grid(row=3, column=1, sticky="ew", padx=10, pady=10)

        # Add brightness slider
        self.bri_label_manual = CTkLabel(self.add_new_light_manual_frame, text="Brightness:100", font=(CTkFont, 20))
        self.bri_label_manual.grid(column=0, row=4, padx=10, pady=10)
        self.bri_val_manual = customtkinter.IntVar()
        self.bri_slider_manual = CTkSlider(self.add_new_light_manual_frame, from_=0, to=200, number_of_steps=20,
                                       variable=self.bri_val_manual,
                                       command=lambda x: self.update_label_bri(x, self.bri_label_manual))
        self.bri_slider_manual.set(100)
        self.bri_slider_manual.grid(row=4, column=1, sticky="ew", padx=10, pady=10)

        # Add position selector
        CTkLabel(self.add_new_light_manual_frame, text="Select position", font=(CTkFont, 20)).grid(column=0, row=5, padx=10, pady=10)
        self.position_select_var_manual = customtkinter.StringVar(value="WHOLE SCREEN")
        self.position_select_manual = CTkComboBox(self.add_new_light_manual_frame, state="readonly",
                                              values=["WHOLE SCREEN", "TOP", "LEFT", "BOTTOM", "RIGHT",
                                                      "TOP-CENTRE", "LEFT-CENTRE", "BOTTOM-CENTRE",
                                                      "RIGHT-CENTRE", "CORNER-TOP-LEFT", "CORNER-BOTTOM-LEFT",
                                                      "CORNER-BOTTOM-RIGHT", "CORNER-TOP-RIGHT"],
                                              variable=self.position_select_var_manual)
        self.position_select_manual.grid(column=1, row=5, sticky="ew", padx=10, pady=10)

        # Add monitor selector
        CTkLabel(self.add_new_light_manual_frame, text="Select monitor", font=(CTkFont, 20)).grid(column=0, row=6, padx=10, pady=10)
        self.monitor_select_var_manual = customtkinter.StringVar(value="1")
        self.monitor_select_manual = CTkComboBox(self.add_new_light_manual_frame, state="readonly",
                                             values=[str(m + 1) for m in range(mon_number() - 1)],
                                             variable=self.monitor_select_var_manual)
        self.monitor_select_manual.grid(column=1, row=6, sticky="ew", padx=10, pady=10)

        # Add enable checkbox
        self.enable_check_var_manual = customtkinter.IntVar()
        self.enable_check_var_manual.set(1)
        self.check_enable_manual = CTkCheckBox(self.add_new_light_manual_frame, text="Enable light",
                                           variable=self.enable_check_var_manual, onvalue=1, offvalue=0,
                                           font=(CTkFont, 20))
        self.check_enable_manual.grid(column=0, row=7, padx=10, pady=10)

        # Add and Back buttons
        CTkButton(self.add_new_light_manual_frame, text="Add Light", command=self.add_light_manual, font=(CTkFont, 20)
                  ).grid(column=1, row=8, pady=20)
        CTkButton(self.add_new_light_manual_frame, text="Back", command=lambda: self.select_frame(self.status_frame),
                  font=(CTkFont, 20)
                  ).grid(column=0, row=8, pady=20)

    def _create_edit_lights_frame(self):
        self.edit_lights_frame.grid_columnconfigure(0, weight=1)
        self.edit_lights_frame.grid_columnconfigure(1, weight=2)

        CTkLabel(self.edit_lights_frame, text="Edit Lights", font=(CTkFont, 26)).grid(column=0, row=0, columnspan=2, pady=15)

        # Create listbox for light selection
        self.edit_list = tk.Listbox(self.edit_lights_frame, selectbackground="#1f538d", fg="#DCE4EE",
                                    height=6, background="grey10", borderwidth=0, highlightthickness=0,
                                    selectforeground="#DCE4EE", activestyle="none", font=(CTkFont, 12))
        self.edit_list.grid(column=0, row=1, rowspan=3, padx=8, pady=8, sticky="ew")
        self.edit_list.bind('<<ListboxSelect>>', self.selected_edit)

        # Add identification button
        CTkButton(self.edit_lights_frame, text="Identify selected", font=(CTkFont, 20),
                 command=lambda: self.identify_edit(self.edit_list.curselection())).grid(row=1, column=1, sticky="w")

        # Add refresh button
        CTkButton(self.edit_lights_frame, text="Refresh", font=(CTkFont, 20),
                 command=self.refresh_lights_list).grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        # Add name entry field
        CTkLabel(self.edit_lights_frame, text="Light Name", font=(CTkFont, 20)).grid(column=0, row=5, padx=5, pady=5)
        self.entry_name_edit = CTkEntry(self.edit_lights_frame, placeholder_text="Light name", font=(CTkFont, 12))
        self.entry_name_edit.grid(column=1, row=5, sticky="ew", padx=5, pady=5)

        # Add saturation slider
        self.sat_label_edit = CTkLabel(self.edit_lights_frame, text="Saturation:100", font=(CTkFont, 20))
        self.sat_label_edit.grid(column=0, row=6, padx=5, pady=5)
        self.sat_val_edit = customtkinter.IntVar()
        self.sat_slider_edit = CTkSlider(self.edit_lights_frame, from_=0, to=200, number_of_steps=20,
                                      variable=self.sat_val_edit,
                                      command=lambda x: self.update_label_sat(x, self.sat_label_edit))
        self.sat_slider_edit.set(100)
        self.sat_slider_edit.grid(row=6, column=1, sticky="ew", padx=5, pady=5)

        # Add brightness slider
        self.bri_label_edit = CTkLabel(self.edit_lights_frame, text="Brightness:100", font=(CTkFont, 20))
        self.bri_label_edit.grid(column=0, row=7, padx=5, pady=5)
        self.bri_val_edit = customtkinter.IntVar()
        self.bri_slider_edit = CTkSlider(self.edit_lights_frame, from_=0, to=200, number_of_steps=20,
                                      variable=self.bri_val_edit,
                                      command=lambda x: self.update_label_bri(x, self.bri_label_edit))
        self.bri_slider_edit.set(100)
        self.bri_slider_edit.grid(row=7, column=1, sticky="ew", padx=5, pady=5)

        # Add position selector
        CTkLabel(self.edit_lights_frame, text="Select position", font=(CTkFont, 20)).grid(column=0, row=8, padx=5, pady=5)
        self.position_select_var_edit = customtkinter.StringVar(value="WHOLE SCREEN")
        self.position_select_edit = CTkComboBox(self.edit_lights_frame, state="readonly",
                                            values=["WHOLE SCREEN", "TOP", "LEFT", "BOTTOM", "RIGHT",
                                                    "TOP-CENTRE", "LEFT-CENTRE", "BOTTOM-CENTRE",
                                                    "RIGHT-CENTRE", "CORNER-TOP-LEFT", "CORNER-BOTTOM-LEFT",
                                                    "CORNER-BOTTOM-RIGHT", "CORNER-TOP-RIGHT"],
                                            variable=self.position_select_var_edit)
        self.position_select_edit.grid(column=1, row=8, sticky="ew", padx=5, pady=5)

        # Add monitor selector
        CTkLabel(self.edit_lights_frame, text="Select monitor", font=(CTkFont, 20)).grid(column=0, row=9, padx=5, pady=5)
        self.monitor_select_var_edit = customtkinter.StringVar(value="1")
        self.monitor_select_edit = CTkComboBox(self.edit_lights_frame, state="readonly",
                                           values=[str(m + 1) for m in range(mon_number() - 1)],
                                           variable=self.monitor_select_var_edit)
        self.monitor_select_edit.grid(column=1, row=9, sticky="ew", padx=5, pady=5)

        # Add enable checkbox
        self.enable_check_var_edit = customtkinter.IntVar()
        self.enable_check_var_edit.set(1)
        self.check_enable_edit = CTkCheckBox(self.edit_lights_frame, text="Enable light",
                                         variable=self.enable_check_var_edit, onvalue=1, offvalue=0,
                                         font=(CTkFont, 20))
        self.check_enable_edit.grid(column=0, row=10, padx=5, pady=5)

        # Add buttons for actions
        CTkButton(self.edit_lights_frame, text="Save Changes", command=self.save_light_changes, font=(CTkFont, 20)
                 ).grid(column=1, row=11, pady=10)
        CTkButton(self.edit_lights_frame, text="Remove Light", command=self.remove_light, font=(CTkFont, 20),
                 fg_color="#FF5555", hover_color="#AA3333"
                 ).grid(column=0, row=11, pady=10)
        CTkButton(self.edit_lights_frame, text="Back", command=lambda: self.select_frame(self.status_frame),
                 font=(CTkFont, 20)
                 ).grid(column=0, row=12, pady=10)

        # Initialize list for storing light IPs
        self.list_items = []

        # Populate edit list when frame is created
        self.refresh_lights_list()

    def _create_edit_settings_frame(self):
        self.edit_settings_frame.grid_columnconfigure(0, weight=1)
        self.edit_settings_frame.grid_columnconfigure(1, weight=2)

        CTkLabel(self.edit_settings_frame, text="Settings", font=(CTkFont, 26)).grid(column=0, row=0, columnspan=2, pady=15)

        # Add FPS setting
        CTkLabel(self.edit_settings_frame, text="FPS:", font=(CTkFont, 20)).grid(column=0, row=1, padx=10, pady=10, sticky="w")
        self.fps_var = customtkinter.StringVar(value=str(self.settings_manager.fps))
        self.fps_entry = CTkEntry(self.edit_settings_frame, textvariable=self.fps_var, font=(CTkFont, 12))
        self.fps_entry.grid(column=1, row=1, padx=10, pady=10, sticky="ew")

        # Add bar correction setting
        CTkLabel(self.edit_settings_frame, text="Bar Correction:", font=(CTkFont, 20)).grid(column=0, row=2, padx=10, pady=10, sticky="w")
        self.bar_correction_var = customtkinter.IntVar(value=self.settings_manager.bar_correction)
        self.bar_correction_checkbox = CTkCheckBox(self.edit_settings_frame, text="",
                                               variable=self.bar_correction_var, onvalue=1, offvalue=0)
        self.bar_correction_checkbox.grid(column=1, row=2, padx=10, pady=10, sticky="w")

        # Add black bar setting
        CTkLabel(self.edit_settings_frame, text="Black Bar:", font=(CTkFont, 20)).grid(column=0, row=3, padx=10, pady=10, sticky="w")
        self.black_bar_var = customtkinter.StringVar(value=str(self.settings_manager.black_bar))
        self.black_bar_entry = CTkEntry(self.edit_settings_frame, textvariable=self.black_bar_var, font=(CTkFont, 12))
        self.black_bar_entry.grid(column=1, row=3, padx=10, pady=10, sticky="ew")

        # Add Color Correction section
        CTkLabel(self.edit_settings_frame, text="Color Correction", font=(CTkFont, 20)).grid(column=0, row=4, columnspan=2, padx=10, pady=(20,5), sticky="w")
        
        # Color correction enable checkbox
        self.color_correction_var = customtkinter.IntVar(value=self.settings_manager.color_correction)
        self.color_correction_checkbox = CTkCheckBox(self.edit_settings_frame, text="Enable Color Correction",
                                                variable=self.color_correction_var, onvalue=1, offvalue=0)
        self.color_correction_checkbox.grid(column=0, row=5, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Red gain slider
        self.red_gain_label = CTkLabel(self.edit_settings_frame, text=f"Red Gain: {self.settings_manager.red_gain}%", font=(CTkFont, 16))
        self.red_gain_label.grid(column=0, row=6, padx=10, pady=5, sticky="w")
        self.red_gain_var = customtkinter.IntVar(value=self.settings_manager.red_gain)
        self.red_gain_slider = CTkSlider(self.edit_settings_frame, from_=50, to=150, number_of_steps=100,
                                     variable=self.red_gain_var,
                                     command=lambda x: self.update_gain_label("red", x))
        self.red_gain_slider.grid(column=1, row=6, padx=10, pady=5, sticky="ew")
        
        # Green gain slider
        self.green_gain_label = CTkLabel(self.edit_settings_frame, text=f"Green Gain: {self.settings_manager.green_gain}%", font=(CTkFont, 16))
        self.green_gain_label.grid(column=0, row=7, padx=10, pady=5, sticky="w")
        self.green_gain_var = customtkinter.IntVar(value=self.settings_manager.green_gain)
        self.green_gain_slider = CTkSlider(self.edit_settings_frame, from_=50, to=150, number_of_steps=100,
                                       variable=self.green_gain_var,
                                       command=lambda x: self.update_gain_label("green", x))
        self.green_gain_slider.grid(column=1, row=7, padx=10, pady=5, sticky="ew")
        
        # Blue gain slider
        self.blue_gain_label = CTkLabel(self.edit_settings_frame, text=f"Blue Gain: {self.settings_manager.blue_gain}%", font=(CTkFont, 16))
        self.blue_gain_label.grid(column=0, row=8, padx=10, pady=5, sticky="w")
        self.blue_gain_var = customtkinter.IntVar(value=self.settings_manager.blue_gain)
        self.blue_gain_slider = CTkSlider(self.edit_settings_frame, from_=50, to=150, number_of_steps=100,
                                      variable=self.blue_gain_var,
                                      command=lambda x: self.update_gain_label("blue", x))
        self.blue_gain_slider.grid(column=1, row=8, padx=10, pady=5, sticky="ew")
        
        # Gamma slider
        self.gamma_label = CTkLabel(self.edit_settings_frame, text=f"Gamma: {self.settings_manager.gamma/100:.1f}", font=(CTkFont, 16))
        self.gamma_label.grid(column=0, row=9, padx=10, pady=5, sticky="w")
        self.gamma_var = customtkinter.IntVar(value=self.settings_manager.gamma)
        self.gamma_slider = CTkSlider(self.edit_settings_frame, from_=50, to=150, number_of_steps=100,
                                  variable=self.gamma_var,
                                  command=lambda x: self.update_gamma_label(x))
        self.gamma_slider.grid(column=1, row=9, padx=10, pady=5, sticky="ew")
        
        # Reset color correction button
        CTkButton(self.edit_settings_frame, text="Reset Color Correction", 
                 command=self.reset_color_correction,
                 fg_color="#FF5555", hover_color="#AA3333").grid(column=0, row=10, padx=10, pady=10)

        # Add save button
        CTkButton(self.edit_settings_frame, text="Save Settings", command=self.save_settings, font=(CTkFont, 20)
                 ).grid(column=1, row=11, padx=10, pady=20)

        # Add back button
        CTkButton(self.edit_settings_frame, text="Back", command=lambda: self.select_frame(self.status_frame),
                 font=(CTkFont, 20)
                 ).grid(column=0, row=11, padx=10, pady=20)

    def update_gain_label(self, color, value):
        """Update the gain label for the specified color"""
        value = int(value)
        if color == "red":
            self.red_gain_label.configure(text=f"Red Gain: {value}%")
        elif color == "green":
            self.green_gain_label.configure(text=f"Green Gain: {value}%")
        elif color == "blue":
            self.blue_gain_label.configure(text=f"Blue Gain: {value}%")

    def update_gamma_label(self, value):
        """Update the gamma label"""
        value = int(value)
        gamma = value / 100
        self.gamma_label.configure(text=f"Gamma: {gamma:.1f}")

    def reset_color_correction(self):
        """Reset color correction settings to default"""
        self.red_gain_slider.set(100)
        self.green_gain_slider.set(100)
        self.blue_gain_slider.set(100)
        self.gamma_slider.set(100)
        self.update_gain_label("red", 100)
        self.update_gain_label("green", 100)
        self.update_gain_label("blue", 100)
        self.update_gamma_label(100)

    def add_light_auto(self):
        selection = self.discovered_list.curselection()
        if not selection:
            return

        ip = self.discovered_list.get(selection[0])
        name = self.entry_name.get() if self.entry_name.get() else ip
        monitor = int(self.monitor_select_var_auto.get())
        position = position_string_to_int(self.position_select_var_auto.get())
        brightness = self.bri_val_auto.get()
        saturation = self.sat_val_auto.get()
        enabled = True if self.enable_check_var_auto.get() == 1 else False

        light_data = [ip, monitor, position, brightness, saturation, name, enabled]
        self.light_manager.add_light(light_data)
        self.light_manager.save()
        self.select_frame(self.status_frame)

        # Reset fields
        self.entry_name.delete(0, tk.END)
        self.sat_slider_auto.set(100)
        self.bri_slider_auto.set(100)
        self.position_select_auto.set("WHOLE SCREEN")
        self.monitor_select_auto.set("1")
        self.enable_check_var_auto.set(1)

    def add_light_manual(self):
        ip = self.entry_ip_manual.get()
        if not validate_ip(ip):
            print("Invalid IP")
            return

        name = self.entry_name_manual.get() if self.entry_name_manual.get() else ip
        monitor = int(self.monitor_select_var_manual.get())
        position = position_string_to_int(self.position_select_var_manual.get())
        brightness = self.bri_val_manual.get()
        saturation = self.sat_val_manual.get()
        enabled = True if self.enable_check_var_manual.get() == 1 else False

        light_data = [ip, monitor, position, brightness, saturation, name, enabled]
        self.light_manager.add_light(light_data)
        self.light_manager.save()
        self.select_frame(self.status_frame)

        # Reset fields
        self.entry_ip_manual.delete(0, tk.END)
        self.entry_name_manual.delete(0, tk.END)
        self.sat_slider_manual.set(100)
        self.bri_slider_manual.set(100)
        self.position_select_manual.set("WHOLE SCREEN")
        self.monitor_select_manual.set("1")
        self.enable_check_var_manual.set(1)

    def select_frame(self, frame: CTkFrame):
        frame.tkraise()

    def close_app(self):
        self.monitor_manager.stop_sync()
        self.destroy()

    def _toggle_run(self, btn_text: tk.StringVar):
        self.run = not self.run
        if self.run:
            btn_text.set("Stop")
            self.monitor_manager.start_sync()
        else:
            btn_text.set("Start")
            self.monitor_manager.stop_sync()

    def _update_lights_text(self):
        self.light_manager.refresh()
        total, connected, active, deactivated, disconnected = self.light_manager.lights_status()
        self.total_lights_text.set("Loaded lights: " + str(total))
        self.connected_label_text.set("Connected lights: " + str(connected))
        self.active_label_text.set("Active lights: " + str(active))
        self.deactivated_label_text.set("Deactivated lights: " + str(deactivated))
        self.disconnected_label_text.set("Disconnected lights: " + str(disconnected))

    def _update_lights_state(self):
        while True:
            self._update_lights_text()
            time.sleep(15)

    def auto_discover(self):
        self.discovered_list.delete(0, tk.END)
        import ifaddr
        def try_adapter(adapter_name):
            try:
                from yeelight import discover_bulbs
                for bulb in discover_bulbs(interface=adapter_name):
                    line = str(bulb)
                    ip = line[line.find("ip") + 6:line.find("port") - 4]
                    if not any(item[0] == ip for item in self.light_manager.connected_lights) and \
                            not any(item[0] == ip for item in self.light_manager.disconnected_lights):
                        self.discovered_list.insert(tk.END, ip)
            except Exception:
                pass

        for adapter in ifaddr.get_adapters():
            if "virtual" in adapter.nice_name.lower():
                continue
            threading.Thread(target=try_adapter, args=(adapter.name,), daemon=True).start()

    def identify(self, selection):
        if selection:
            ip = self.discovered_list.get(selection[0])
            from light import Light
            Light(ip).identify()

    def identify_edit(self, selection):
        if selection:
            index = selection[0]
            ip = self.list_items[index]
            from light import Light
            Light(ip).identify()

    def selected_edit(self, event):
        if not self.edit_list.curselection():
            return
            
        index = self.edit_list.curselection()[0]
        selected_item = None
        for item in self.light_manager.connected_lights:
            if self.list_items[index] == item[0]:
                selected_item = item
                break
        if not selected_item:
            for item in self.light_manager.disconnected_lights:
                if self.list_items[index] == item[0]:
                    selected_item = item
                    break
        if selected_item:
            self.sat_slider_edit.set(selected_item[4])
            self.update_label_sat(self.sat_val_edit.get(), self.sat_label_edit)
            self.bri_slider_edit.set(selected_item[3])
            self.update_label_bri(self.bri_val_edit.get(), self.bri_label_edit)
            self.entry_name_edit.delete(0, tk.END)
            self.entry_name_edit.insert(0, selected_item[5])
            self.position_select_var_edit.set(position_int_to_string(selected_item[2]))
            self.monitor_select_var_edit.set(str(selected_item[1]))
            if selected_item[6]:
                self.enable_check_var_edit.set(1)
                self.check_enable_edit.select()
            else:
                self.enable_check_var_edit.set(0)
                self.check_enable_edit.deselect()

    def update_label_sat(self, val, label):
        label.configure(text="Saturation:" + str(int(val)))

    def update_label_bri(self, val, label):
        label.configure(text="Brightness:" + str(int(val)))

    def refresh_lights_list(self):
        # Clear and repopulate list of lights
        self.edit_list.delete(0, tk.END)
        self.list_items = []

        # Add connected lights first
        for light in self.light_manager.connected_lights:
            self.edit_list.insert(tk.END, f"{light[5]} ({light[0]})")
            self.list_items.append(light[0])

        # Then add disconnected lights
        for light in self.light_manager.disconnected_lights:
            self.edit_list.insert(tk.END, f"{light[5]} ({light[0]}) - Disconnected")
            self.list_items.append(light[0])

    def save_light_changes(self):
        selection = self.edit_list.curselection()
        if not selection:
            return

        ip = self.list_items[selection[0]]
        name = self.entry_name_edit.get()
        monitor = int(self.monitor_select_var_edit.get())
        position = position_string_to_int(self.position_select_var_edit.get())
        brightness = self.bri_val_edit.get()
        saturation = self.sat_val_edit.get()
        enabled = bool(self.enable_check_var_edit.get())

        # Update light in connected or disconnected list
        for i, light in enumerate(self.light_manager.connected_lights):
            if light[0] == ip:
                self.light_manager.connected_lights[i] = [ip, monitor, position, brightness, saturation, name, enabled]
                # Update light object if it exists
                for light_obj in self.light_manager.lights:
                    if light_obj.ip == ip:
                        light_obj.set_prop([monitor, position, brightness, saturation, name, enabled])
                break

        for i, light in enumerate(self.light_manager.disconnected_lights):
            if light[0] == ip:
                self.light_manager.disconnected_lights[i] = [ip, monitor, position, brightness, saturation, name, enabled]
                break

        self.light_manager.save()
        self.refresh_lights_list()
        self._update_lights_text()

    def remove_light(self):
        selection = self.edit_list.curselection()
        if not selection:
            return

        ip = self.list_items[selection[0]]

        # Remove from connected lights and light objects
        for i, light in enumerate(self.light_manager.connected_lights[:]):
            if light[0] == ip:
                del self.light_manager.connected_lights[i]
                break

        for i, light_obj in enumerate(self.light_manager.lights[:]):
            if light_obj.ip == ip:
                del self.light_manager.lights[i]
                break

        # Remove from disconnected lights
        for i, light in enumerate(self.light_manager.disconnected_lights[:]):
            if light[0] == ip:
                del self.light_manager.disconnected_lights[i]
                break

        self.light_manager.save()
        self.refresh_lights_list()
        self._update_lights_text()

    def save_settings(self):
        try:
            fps = int(self.fps_var.get())
            if fps < 1:
                fps = 1
            elif fps > 30:
                fps = 30
            black_bar = int(self.black_bar_var.get())
            if black_bar < 0:
                black_bar = 0

            self.settings_manager.fps = fps
            self.settings_manager.bar_correction = self.bar_correction_var.get()
            self.settings_manager.black_bar = black_bar
            
            # Save color correction settings
            self.settings_manager.color_correction = self.color_correction_var.get()
            self.settings_manager.red_gain = self.red_gain_var.get()
            self.settings_manager.green_gain = self.green_gain_var.get()
            self.settings_manager.blue_gain = self.blue_gain_var.get()
            self.settings_manager.gamma = self.gamma_var.get()

            all_lights = self.light_manager.connected_lights + self.light_manager.disconnected_lights
            self.settings_manager.save(all_lights)
        except ValueError:
            # Handle invalid input
            pass
