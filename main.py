import threading
import tkinter as tk

import customtkinter
import ifaddr
from customtkinter import *
from yeelight import discover_bulbs

from light import *
from save_data import *
from screenshot import *

connected_lights = []
disconnected_lights = []
lights = []
run = False
rate = 0


def position_int_to_string(pos):
    if pos == 0:
        pos = "WHOLE SCREEN"
    elif pos == 1:
        pos = "TOP"
    elif pos == 2:
        pos = "LEFT"
    elif pos == 3:
        pos = "BOTTOM"
    elif pos == 4:
        pos = "RIGHT"
    elif pos == 5:
        pos = "TOP-CENTRE"
    elif pos == 6:
        pos = "LEFT-CENTRE"
    elif pos == 7:
        pos = "BOTTOM-CENTRE"
    elif pos == 8:
        pos = "RIGHT-CENTRE"
    elif pos == 9:
        pos = "CORNER-TOP-LEFT"
    elif pos == 10:
        pos = "CORNER-BOTTOM-LEFT"
    elif pos == 11:
        pos = "CORNER-BOTTOM-RIGHT"
    elif pos == 12:
        pos = "CORNER-TOP-RIGHT"
    return pos


def position_string_to_int(pos):
    if pos == "WHOLE SCREEN":
        pos = 0
    elif pos == "TOP":
        pos = 1
    elif pos == "LEFT":
        pos = 2
    elif pos == "BOTTOM":
        pos = 3
    elif pos == "RIGHT":
        pos = 4
    elif pos == "TOP-CENTRE":
        pos = 5
    elif pos == "LEFT-CENTRE":
        pos = 6
    elif pos == "BOTTOM-CENTRE":
        pos = 7
    elif pos == "RIGHT-CENTRE":
        pos = 8
    elif pos == "CORNER-TOP-LEFT":
        pos = 9
    elif pos == "CORNER-BOTTOM-LEFT":
        pos = 10
    elif pos == "CORNER-BOTTOM-RIGHT":
        pos = 11
    elif pos == "CORNER-TOP-RIGHT":
        pos = 12
    return pos


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def load_settings():
    global fps
    global bar_correction
    global rate
    global bar_update
    settings = load()
    bar_correction = settings['bar_correction']
    fps = settings['fps']
    bar_update = settings['black_bar']
    rate = 1 / fps
    l = settings['lights']
    for x in l:
        if light_online(x[0]):
            connected_lights.append(x[:])
            ip = x[0]
            x.pop(0)
            light = Light(ip)
            light.set_prop(x)
            lights.append(light)
        else:
            disconnected_lights.append(x)


def save_settings():
    global fps
    global bar_correction
    global bar_update
    l = []
    l.extend(connected_lights)
    l.extend(disconnected_lights)
    settings = {"fps": fps, 'bar_correction': bar_correction, 'lights': l, 'black_bar': bar_update}
    save(settings)


def lights_status():
    connected = len(connected_lights)
    active = 0
    deactivated = 0
    disconnected = len(disconnected_lights)
    for l in lights:
        if l.enable:
            active += 1
        else:
            deactivated += 1
    return connected + disconnected, connected, active, deactivated, disconnected


def refresh_connected():
    if run is True:
        pass
    for i, l in enumerate(lights):
        if run is False and l.light_online() == 0:
            disconnected_lights.append(connected_lights[i])
            connected_lights.pop(i)
            lights.pop(i)


def refresh_disconnected():
    for i, l in enumerate(disconnected_lights):
        if light_online(l[0]):
            x = l
            ip = l[0]
            l.pop(0)
            light = Light(ip)
            light.set_prop(l)
            lights.append(light)
            connected_lights.append(x)
            disconnected_lights.pop(i)


def sync_lights(i):
    global bar_correction
    global bar_update
    global fps

    def light_connected():
        for x in lights:
            if x.get_monitor() == i and x.enable == True:
                return True
        return False

    m = Monitor(i, bar_correction, bar_update * fps / 2)
    k = 0
    while run:
        t1 = time.time()
        if light_connected():
            s = m.get_mon_hsv()
            for x in lights:
                if x.get_monitor() == i:
                    x.set_hsv(s, rate)
        k += 1
        t = time.time() - t1
        if rate > t:
            time.sleep(rate - t)
    time.sleep(0.25)
    for x in lights:
        if x.get_monitor() == i and x.enable == True:
            x.revert_to_initial()
    pass


def start():
    # print(1)
    for i in range(1, mon_number()):
        t = threading.Thread(target=sync_lights, args=(i,))
        t.start()


def update_lights_text():
    refresh_disconnected()
    refresh_connected()
    t, c, a, d, dc = lights_status()
    global total_lights_text
    global connected_label_text
    global active_label_text
    global deactivated_label_text
    global disconnected_label_text
    total_lights_text.set('Loaded lights:' + str(t))
    connected_label_text.set('Connected lights:' + str(c))
    active_label_text.set('Active lights:' + str(a))
    deactivated_label_text.set('Deactivated lights:' + str(d))
    disconnected_label_text.set('Disconnected lights:' + str(dc))


def update_lights_state():
    while True:
        update_lights_text()
        time.sleep(15)


def main_menu():
    def disable_buttons():
        global add_new_light_button
        global add_new_light_manual_button
        global edit_lights_button
        global edit_settings_button
        add_new_light_button.configure(state='disabled')
        add_new_light_manual_button.configure(state='disabled')
        edit_lights_button.configure(state='disabled')
        edit_settings_button.configure(state='disabled')

    def enable_buttons():
        global add_new_light_button
        global add_new_light_manual_button
        global edit_lights_button
        global edit_settings_button
        add_new_light_button.configure(state='normal')
        add_new_light_manual_button.configure(state='normal')
        edit_lights_button.configure(state='normal')
        edit_settings_button.configure(state='normal')

    def run_button_click(text):
        global run
        run = not run
        if run:
            disable_buttons()
            text.set('Stop')
        else:
            enable_buttons()
            text.set('Start')
        start()

    def close_main_window():
        global run
        run = False
        root.destroy()

    def select_frame(frame):
        frame.tkraise()

    def select_auto_add(frame):
        frame.tkraise()
        auto_discover()

    def select_edit(frame):
        frame.tkraise()
        add_in_list()
        reset_fields_edit()

    def select_settings(frame):
        frame.tkraise()
        reset_fields_settings()

    customtkinter.set_default_color_theme("dark-blue")
    root = CTk()
    # main_menu_frame
    main_menu_frame = CTkFrame(root)
    run_button_text = customtkinter.StringVar(value='Start')
    run_button = CTkButton(main_menu_frame, textvariable=run_button_text,
                           command=lambda: (run_button_click(run_button_text), select_frame(status_frame))).pack(
        padx=16, pady=8, fill='both')
    global total_lights_text
    global connected_label_text
    global active_label_text
    global deactivated_label_text
    global disconnected_label_text
    total_lights_text = customtkinter.StringVar(value='Loaded lights:')
    connected_label_text = customtkinter.StringVar(value='Connected lights:')
    active_label_text = customtkinter.StringVar(value='Active lights:')
    deactivated_label_text = customtkinter.StringVar(value='Deactivated lights:')
    disconnected_label_text = customtkinter.StringVar(value='Disconnected lights:')
    total_lights_label = CTkLabel(main_menu_frame, textvariable=total_lights_text).pack(fill='x')
    connected_label = CTkLabel(main_menu_frame, textvariable=connected_label_text).pack(fill='x')
    active_label = CTkLabel(main_menu_frame, textvariable=active_label_text).pack(fill='x')
    deactivated_label = CTkLabel(main_menu_frame, textvariable=deactivated_label_text).pack(fill='x')
    disconnected_label = CTkLabel(main_menu_frame, textvariable=disconnected_label_text).pack(fill='x')
    refresh_button = CTkButton(main_menu_frame, text='Refresh lights', command=update_lights_text).pack(padx=16, pady=8,
                                                                                                        fill='both')
    exit_button = CTkButton(main_menu_frame, text='Exit', command=close_main_window).pack(padx=16, pady=8, fill='both')
    root.grid_rowconfigure(0, minsize=288, weight=1)
    root.grid_rowconfigure(1, minsize=236, weight=1)
    root.grid_columnconfigure(0, minsize=200, weight=1)
    root.grid_columnconfigure(1, minsize=600, weight=3)
    main_menu_frame.grid(row=0, column=0, sticky=N + S + E + W, padx=8, pady=8)
    # config_buttons_frame
    config_buttons_frame = CTkFrame(root)
    status_page_button = CTkButton(config_buttons_frame, text='Status page',
                                   command=lambda: select_frame(status_frame)).pack(padx=16, pady=8, fill='x')
    global add_new_light_button
    global add_new_light_manual_button
    global edit_lights_button
    global edit_settings_button
    add_new_light_button = CTkButton(config_buttons_frame, text='Add new light',
                                     command=lambda: select_auto_add(add_new_light_frame))
    add_new_light_button.pack(padx=16, pady=8, fill='x')
    add_new_light_manual_button = CTkButton(config_buttons_frame, text='Manually add light',
                                            command=lambda: select_frame(add_new_light_manual_frame))
    add_new_light_manual_button.pack(padx=16, pady=8, fill='x')
    edit_lights_button = CTkButton(config_buttons_frame, text='Edit lights',
                                   command=lambda: select_edit(edit_lights_frame))
    edit_lights_button.pack(padx=16, pady=8, fill='x')
    edit_settings_button = CTkButton(config_buttons_frame, text='Settings',
                                     command=lambda: select_settings(edit_settings_frame))
    edit_settings_button.pack(padx=16, pady=8, fill='x')

    config_buttons_frame.grid(row=1, column=0, sticky=N + S + E + W, padx=8, pady=8)
    # status frame
    status_frame = CTkFrame(root)
    CTkLabel(status_frame, text='Status page').pack()
    status_frame.grid(row=0, column=1, rowspan=2, sticky=N + S + E + W, padx=8, pady=8)
    # add light frame
    add_new_light_frame = CTkFrame(root)
    add_new_light_frame.grid_columnconfigure(0, minsize=200, weight=1)
    add_new_light_frame.grid_columnconfigure(1, minsize=200, weight=1)
    add_new_light_frame.grid_columnconfigure(2, minsize=200, weight=1)
    CTkLabel(add_new_light_frame, text='Add new light', font=(CTkFont, 26)).grid(column=0, row=0, columnspan=3, pady=15)
    discovered_list = tk.Listbox(master=add_new_light_frame, selectbackground='#1f538d', fg='#DCE4EE', height=6)
    discovered_list.grid(column=0, row=1, rowspan=3, padx=8, pady=8, sticky=E + W)
    discovered_list.configure(background="grey10", borderwidth=0, highlightthickness=0, selectforeground='#DCE4EE',
                              activestyle='none', font=(CTkFont, 12))

    def auto_discover():
        def try_one_adapter(z):
            try:
                d = discover_bulbs(interface=z)
                for x in d:
                    line = str(x)
                    k1 = line.find('ip') + 6
                    k2 = line.find('port') - 4
                    ip = line[k1:k2]
                    new_bulb = True
                    for b in connected_lights:
                        if b[0] == ip:
                            new_bulb = False
                            break
                    for b in disconnected_lights:
                        if b[0] == ip:
                            new_bulb = False
                            break
                    if new_bulb:
                        discovered_list.insert(END, ip)
            except:
                pass

        discovered_list.delete(0, END)
        adap = ifaddr.get_adapters()
        for a in adap:
            k = str(a.nice_name)
            if 'virtual' in k:
                continue
            elif 'Virtual' in k:
                continue
            a = a.name
            o = threading.Thread(target=try_one_adapter, args=(a,))
            o.start()

    def identify(sel):
        if sel == ():
            pass
        else:
            s = discovered_list.get(sel[0])
            Light(s).identify()

    CTkLabel(add_new_light_frame, text='Nu gasesti becu', font=(CTkFont, 20)).grid(row=1, column=1)
    CTkButton(add_new_light_frame, text='Identify selected', font=(CTkFont, 20),
              command=lambda: identify(discovered_list.curselection())).grid(row=1, column=2, sticky=W)
    CTkButton(add_new_light_frame, text='Refresh', command=auto_discover, font=(CTkFont, 20)).grid(row=4, column=0,
                                                                                                   sticky=E + W, padx=5,
                                                                                                   pady=5)
    CTkLabel(add_new_light_frame, text='Light name', font=(CTkFont, 20)).grid(column=1, row=2, columnspan=2, sticky=W,
                                                                              padx=5, pady=5)
    entry_name = customtkinter.CTkEntry(master=add_new_light_frame, placeholder_text="Light name", font=(CTkFont, 12))
    entry_name.grid(column=1, row=3, columnspan=2, sticky=W + E, padx=5, pady=5)
    sat_label = CTkLabel(add_new_light_frame, text='Saturation:100', font=(CTkFont, 20))
    sat_label.grid(column=0, row=5, padx=5, pady=5)
    sat_val = customtkinter.IntVar()
    sat_slider = CTkSlider(add_new_light_frame, from_=0, to=200, number_of_steps=20, variable=sat_val,
                           command=lambda x: update_label_sat(x, sat_label))
    sat_slider.set(100)
    sat_slider.grid(row=5, column=1, columnspan=2, sticky=E + W, padx=5, pady=5)

    bri_label = CTkLabel(add_new_light_frame, text='Brightness:100', font=(CTkFont, 20))
    bri_label.grid(column=0, row=6, padx=5, pady=5)
    bri_val = customtkinter.IntVar()
    bri_slider = CTkSlider(add_new_light_frame, from_=0, to=200, number_of_steps=20, variable=bri_val,
                           command=lambda x: update_label_bri(x, bri_label))
    bri_slider.set(100)
    bri_slider.grid(row=6, column=1, columnspan=2, sticky=E + W, padx=5, pady=5)
    CTkLabel(add_new_light_frame, text='Select position', font=(CTkFont, 20)).grid(column=0, row=7, padx=5, pady=5)
    position_select_var = customtkinter.StringVar(value="WHOLE SCREEN")
    position_select = customtkinter.CTkComboBox(master=add_new_light_frame, state="readonly",
                                                values=["WHOLE SCREEN", "TOP", "LEFT", "BOTTOM", "RIGHT", "TOP-CENTRE",
                                                        "LEFT-CENTRE", "BOTTOM-CENTRE", "RIGHT-CENTRE",
                                                        "CORNER-TOP-LEFT", "CORNER-BOTTOM-LEFT", "CORNER-BOTTOM-RIGHT",
                                                        "CORNER-TOP-RIGHT"], variable=position_select_var)
    position_select.grid(column=1, row=7, sticky=E + W, padx=5, pady=5)
    CTkLabel(add_new_light_frame, text='Select monitor', font=(CTkFont, 20)).grid(column=0, row=8, padx=5, pady=5)
    monitor_select_var = customtkinter.StringVar(value="1")
    monitor_select = customtkinter.CTkComboBox(master=add_new_light_frame, state="readonly",
                                               values=[str(m + 1) for m in range(mon_number() - 1)],
                                               variable=monitor_select_var)
    monitor_select.grid(column=1, row=8, sticky=E + W, padx=5, pady=5)
    enable_check_var = customtkinter.IntVar()
    enable_check_var.set(1)
    check_enable = customtkinter.CTkCheckBox(master=add_new_light_frame, text="Enable light", variable=enable_check_var,
                                             onvalue=1, offvalue=2, font=(CTkFont, 20))
    check_enable.grid(column=0, row=9, padx=5, pady=5)

    def reset_fields_auto():
        sat_slider.set(100)
        update_label_sat(sat_val.get(), sat_label)
        bri_slider.set(100)
        update_label_bri(bri_val.get(), bri_label)
        entry_name.delete(0, END)
        position_select.set('WHOLE SCREEN')
        enable_check_var.set(1)
        monitor_select_var.set('1')

    def add_light():
        id = discovered_list.curselection()
        if id == ():
            return
        id = id[0]
        ip = discovered_list.get(id)
        sat = sat_val.get()
        bri = bri_val.get()
        name = entry_name.get()
        pos = position_string_to_int(position_select_var.get())
        if enable_check_var.get() == 1:
            enable = True
        else:
            enable = False
        mon = int(monitor_select_var.get())
        connected_lights.append([ip, mon, pos, bri, sat, name, enable])
        l = Light(ip)
        l.set_prop([mon, pos, bri, sat, name, enable])
        lights.append(l)
        save_settings()
        discovered_list.delete(id)
        reset_fields_auto()

    def back_auto():
        reset_fields_auto()
        select_frame(status_frame)

    CTkButton(master=add_new_light_frame, text='Add light', command=add_light, font=(CTkFont, 20)).grid(column=1,
                                                                                                        row=10, pady=20)
    CTkButton(master=add_new_light_frame, text='Back', command=back_auto, font=(CTkFont, 20)).grid(column=0, row=10,
                                                                                                   pady=20)
    add_new_light_frame.grid(row=0, column=1, rowspan=2, sticky=N + S + E + W, padx=8, pady=8)
    # manual add light frame
    add_new_light_manual_frame = CTkFrame(root)
    add_new_light_manual_frame.grid_columnconfigure(0, minsize=200, weight=1)
    add_new_light_manual_frame.grid_columnconfigure(1, minsize=400, weight=2)
    CTkLabel(add_new_light_manual_frame, text='Manually add light', font=(CTkFont, 26)).grid(column=0, row=0, padx=10,
                                                                                             pady=20, columnspan=2)
    CTkLabel(add_new_light_manual_frame, text='Light ip', font=(CTkFont, 20)).grid(column=0, row=1, padx=10, pady=10)
    # entry_ip_var=customtkinter.StringVar()
    entry_ip_man = customtkinter.CTkEntry(master=add_new_light_manual_frame, placeholder_text="192.168.xxx.xxx",
                                          font=(CTkFont, 12))
    entry_ip_man.grid(column=1, row=1, sticky=E + W, padx=10, pady=10)
    sat_label_man = CTkLabel(add_new_light_manual_frame, text='Saturation:100', font=(CTkFont, 20))
    sat_label_man.grid(column=0, row=2, padx=10, pady=10)

    def update_label_sat(val, label):
        label.configure(text='Saturation:' + str(int(val)))

    sat_val_man = customtkinter.IntVar()
    sat_slider_man = CTkSlider(add_new_light_manual_frame, from_=0, to=200, number_of_steps=20, variable=sat_val_man,
                               command=lambda x: update_label_sat(x, sat_label_man))
    sat_slider_man.set(100)
    sat_slider_man.grid(row=2, column=1, padx=10, pady=10, sticky=E + W)

    bri_label_man = CTkLabel(add_new_light_manual_frame, text='Brightness:100', font=(CTkFont, 20))
    bri_label_man.grid(column=0, row=3, padx=10, pady=10)

    def update_label_bri(val, label):
        label.configure(text='Brightness:' + str(int(val)))

    bri_val_man = customtkinter.IntVar()
    bri_slider_man = CTkSlider(add_new_light_manual_frame, from_=0, to=200, number_of_steps=20, variable=bri_val_man,
                               command=lambda x: update_label_bri(x, bri_label_man))
    bri_slider_man.set(100)
    bri_slider_man.grid(row=3, column=1, padx=10, pady=10, sticky=E + W)
    CTkLabel(add_new_light_manual_frame, text='Light name', font=(CTkFont, 20)).grid(column=0, row=4, padx=10, pady=10)
    entry_name_man = customtkinter.CTkEntry(master=add_new_light_manual_frame, placeholder_text="Light name",
                                            font=(CTkFont, 12))
    entry_name_man.grid(column=1, row=4, padx=10, pady=10, sticky=E + W)
    CTkLabel(add_new_light_manual_frame, text='Select position', font=(CTkFont, 20)).grid(column=0, row=5, padx=10,
                                                                                          pady=10)
    position_select_var_man = customtkinter.StringVar(value="WHOLE SCREEN")
    position_select_man = customtkinter.CTkComboBox(master=add_new_light_manual_frame, state="readonly",
                                                    values=["WHOLE SCREEN", "TOP", "LEFT", "BOTTOM", "RIGHT",
                                                            "TOP-CENTRE", "LEFT-CENTRE", "BOTTOM-CENTRE",
                                                            "RIGHT-CENTRE", "CORNER-TOP-LEFT", "CORNER-BOTTOM-LEFT",
                                                            "CORNER-BOTTOM-RIGHT", "CORNER-TOP-RIGHT"],
                                                    variable=position_select_var_man)
    position_select_man.grid(column=1, row=5, padx=10, pady=10, sticky=E + W)
    enable_check_var_man = customtkinter.IntVar()
    enable_check_var_man.set(1)
    check_enable_man = customtkinter.CTkCheckBox(master=add_new_light_manual_frame, text="Enable light",
                                                 variable=enable_check_var_man, onvalue=1, offvalue=2,
                                                 font=(CTkFont, 20))
    check_enable_man.grid(column=0, row=6, padx=10, pady=10)
    CTkLabel(add_new_light_manual_frame, text='Select monitor', font=(CTkFont, 20)).grid(column=0, row=7, padx=10,
                                                                                         pady=10)
    monitor_select_var_man = customtkinter.StringVar(value="1")
    monitor_select_man = customtkinter.CTkComboBox(master=add_new_light_manual_frame, state="readonly",
                                                   values=[str(m + 1) for m in range(mon_number() - 1)],
                                                   variable=monitor_select_var_man)
    monitor_select_man.grid(column=1, row=7, padx=10, pady=10, sticky=E + W)

    def reset_fields_man():
        entry_ip_man.delete(0, END)
        sat_slider_man.set(100)
        update_label_sat(sat_val_man.get(), sat_label_man)
        bri_slider_man.set(100)
        update_label_bri(bri_val_man.get(), bri_label_man)
        entry_name_man.delete(0, END)
        position_select_man.set('WHOLE SCREEN')
        enable_check_var_man.set(1)
        monitor_select_var_man.set('1')

    def back_to_status_man():
        reset_fields_man()
        select_frame(status_frame)

    def add_light_man():
        ip = entry_ip_man.get()
        if validate_ip(ip):
            if light_online(ip):
                sat = sat_val_man.get()
                bri = bri_val_man.get()
                name = entry_name_man.get()
                pos = position_string_to_int(position_select_var_man.get())
                if enable_check_var_man.get() == 1:
                    enable = True
                else:
                    enable = False
                mon = int(monitor_select_var_man.get())
                connected_lights.append([ip, mon, pos, bri, sat, name, enable])
                l = Light(ip)
                l.set_prop([mon, pos, bri, sat, name, enable])
                lights.append(l)
                save_settings()
            else:
                # add to disconnected
                pass
            reset_fields_man()
        else:
            # wrong ip
            pass

    CTkButton(master=add_new_light_manual_frame, text='Add light', command=add_light_man, font=(CTkFont, 20)).grid(
        column=1, row=8, sticky=E + W, pady=30, padx=45)
    CTkButton(master=add_new_light_manual_frame, text='Back', command=back_to_status_man, font=(CTkFont, 20)).grid(
        column=0, row=8, sticky=E + W, pady=30, padx=45)
    add_new_light_manual_frame.grid(row=0, column=1, rowspan=2, sticky=N + S + E + W, padx=8, pady=8)
    # edit light frame
    edit_lights_frame = CTkFrame(root)
    edit_lights_frame.grid_columnconfigure(0, minsize=200, weight=1)
    edit_lights_frame.grid_columnconfigure(1, minsize=200, weight=1)
    edit_lights_frame.grid_columnconfigure(2, minsize=200, weight=1)
    CTkLabel(edit_lights_frame, text='Edit lights', font=(CTkFont, 26)).grid(column=0, row=0, columnspan=3, pady=15)
    list_items = []

    def selected_edit(e):
        i = edit_list.curselection()[0]
        for l in connected_lights:
            if list_items[i] == l[0]:
                x = l
        for l in disconnected_lights:
            if list_items[i] == l[0]:
                x = l
        sat_slider_edit.set(x[4])
        update_label_sat(sat_val_edit.get(), sat_label_edit)
        bri_slider_edit.set(x[3])
        update_label_bri(bri_val_edit.get(), bri_label_edit)
        entry_name_edit.delete(0, END)
        entry_name_edit.insert(0, x[5])
        position_select_var_edit.set(position_int_to_string(x[2]))
        monitor_select_var_edit.set(str(x[1]))
        if x[6]:
            enable_check_var_edit.set(1)
            check_enable_edit.select()
        else:
            enable_check_var_edit.set(0)
            check_enable_edit.deselect()

    edit_list = tk.Listbox(master=edit_lights_frame, selectbackground='#1f538d', fg='#DCE4EE', height=6)
    edit_list.grid(column=0, row=1, rowspan=3, padx=8, pady=8, sticky=E + W)
    edit_list.configure(background="grey10", borderwidth=0, highlightthickness=0, selectforeground='#DCE4EE',
                        activestyle='none', font=(CTkFont, 12))
    edit_list.bind('<<ListboxSelect>>', selected_edit)

    def add_in_list():
        nonlocal list_items
        list_items = []
        edit_list.delete(0, END)
        for l in connected_lights:
            edit_list.insert(END, l[5])
            list_items.append(l[0])
        for l in disconnected_lights:
            edit_list.insert(END, l[5])
            list_items.append(l[0])

    def identify(sel):
        if sel == ():
            pass
        else:
            s = (sel[0])
            ip = list_items[s]
            for l in connected_lights:
                if ip == l[0]:
                    Light(ip).identify()
                    return

    CTkLabel(edit_lights_frame, text='Nu gasesti becu', font=(CTkFont, 20)).grid(row=1, column=1)
    CTkButton(edit_lights_frame, text='Identify selected', font=(CTkFont, 20),
              command=lambda: identify(edit_list.curselection())).grid(row=1, column=2, sticky=W)
    CTkLabel(edit_lights_frame, text='Light name', font=(CTkFont, 20)).grid(column=1, row=2, columnspan=2, sticky=W,
                                                                            padx=5, pady=5)
    entry_name_edit = customtkinter.CTkEntry(master=edit_lights_frame, placeholder_text="Light name",
                                             font=(CTkFont, 12))
    entry_name_edit.grid(column=1, row=3, columnspan=2, sticky=W + E, padx=5, pady=5)
    sat_label_edit = CTkLabel(edit_lights_frame, text='Saturation:100', font=(CTkFont, 20))
    sat_label_edit.grid(column=0, row=5, padx=5, pady=5)
    sat_val_edit = customtkinter.IntVar()
    sat_slider_edit = CTkSlider(edit_lights_frame, from_=0, to=200, number_of_steps=20, variable=sat_val_edit,
                                command=lambda x: update_label_sat(x, sat_label_edit))
    sat_slider_edit.set(100)
    sat_slider_edit.grid(row=5, column=1, columnspan=2, sticky=E + W, padx=5, pady=5)
    bri_label_edit = CTkLabel(edit_lights_frame, text='Brightness:100', font=(CTkFont, 20))
    bri_label_edit.grid(column=0, row=6, padx=5, pady=5)
    bri_val_edit = customtkinter.IntVar()
    bri_slider_edit = CTkSlider(edit_lights_frame, from_=0, to=200, number_of_steps=20, variable=bri_val_edit,
                                command=lambda x: update_label_bri(x, bri_label_edit))
    bri_slider_edit.set(100)
    bri_slider_edit.grid(row=6, column=1, columnspan=2, sticky=E + W, padx=5, pady=5)
    CTkLabel(edit_lights_frame, text='Select position', font=(CTkFont, 20)).grid(column=0, row=7, padx=5, pady=5)
    position_select_var_edit = customtkinter.StringVar(value="WHOLE SCREEN")
    position_select_edit = customtkinter.CTkComboBox(master=edit_lights_frame, state="readonly",
                                                     values=["WHOLE SCREEN", "TOP", "LEFT", "BOTTOM", "RIGHT",
                                                             "TOP-CENTRE", "LEFT-CENTRE", "BOTTOM-CENTRE",
                                                             "RIGHT-CENTRE", "CORNER-TOP-LEFT", "CORNER-BOTTOM-LEFT",
                                                             "CORNER-BOTTOM-RIGHT", "CORNER-TOP-RIGHT"],
                                                     variable=position_select_var_edit)
    position_select_edit.grid(column=1, row=7, sticky=E + W, padx=5, pady=5)
    CTkLabel(edit_lights_frame, text='Select monitor', font=(CTkFont, 20)).grid(column=0, row=8, padx=5, pady=5)
    monitor_select_var_edit = customtkinter.StringVar(value="1")
    monitor_select_edit = customtkinter.CTkComboBox(master=edit_lights_frame, state="readonly",
                                                    values=[str(m + 1) for m in range(mon_number() - 1)],
                                                    variable=monitor_select_var_edit)
    monitor_select_edit.grid(column=1, row=8, sticky=E + W, padx=5, pady=5)
    enable_check_var_edit = customtkinter.IntVar()
    enable_check_var_edit.set(1)
    check_enable_edit = customtkinter.CTkCheckBox(master=edit_lights_frame, text="Enable light",
                                                  variable=enable_check_var_edit, onvalue=1, offvalue=2,
                                                  font=(CTkFont, 20))
    check_enable_edit.grid(column=0, row=9, padx=5, pady=5)

    def reset_fields_edit():
        sat_slider_edit.set(100)
        update_label_sat(sat_val_edit.get(), sat_label_edit)
        bri_slider_edit.set(100)
        bri_slider_edit.set(100)
        update_label_bri(bri_val_edit.get(), bri_label_edit)
        entry_name_edit.delete(0, END)
        position_select_edit.set('WHOLE SCREEN')
        enable_check_var_edit.set(1)
        monitor_select_var_edit.set('1')

    def delete_light():
        i = edit_list.curselection()
        if i == ():
            return
        i = i[0]
        for k, x in enumerate(connected_lights):
            if list_items[i] == x[0]:
                connected_lights.pop(k)
                lights.pop(k)
                edit_list.delete(i)
                reset_fields_edit()
                return
        for k, x in enumerate(disconnected_lights):
            if list_items[i] == x[0]:
                disconnected_lights.pop(k)
                edit_list.delete(i)
                reset_fields_edit()
                return

    def save_light_settings():
        i = edit_list.curselection()
        if i == ():
            return
        i = i[0]
        for k, x in enumerate(connected_lights):
            if list_items[i] == x[0]:
                connected_lights[k][1] = int(monitor_select_var_edit.get())
                connected_lights[k][2] = position_string_to_int(position_select_var_edit.get())
                connected_lights[k][3] = bri_val_edit.get()
                connected_lights[k][4] = sat_val_edit.get()
                connected_lights[k][5] = entry_name_edit.get()
                if enable_check_var_edit.get() == 1:
                    connected_lights[k][6] = True
                else:
                    connected_lights[k][6] = False
                lights[k].set_prop(connected_lights[k][1:])
                save_settings()
                return
        for k, x in enumerate(disconnected_lights):
            if list_items[i] == x[0]:
                disconnected_lights[k][1] = int(monitor_select_var_edit.get())
                disconnected_lights[k][2] = position_string_to_int(position_select_var_edit.get())
                disconnected_lights[k][3] = bri_val_edit.get()
                disconnected_lights[k][4] = sat_val_edit.get()
                disconnected_lights[k][5] = entry_name_edit.get()
                if enable_check_var_edit.get() == 1:
                    disconnected_lights[k][6] = True
                else:
                    disconnected_lights[k][6] = False
                save_settings()
                return

    def back_edit():
        select_frame(status_frame)
        reset_fields_edit()

    CTkButton(master=edit_lights_frame, text='Save light', command=save_light_settings, font=(CTkFont, 20)).grid(
        column=1, row=10, pady=20)
    CTkButton(master=edit_lights_frame, text='Back', command=back_edit, font=(CTkFont, 20)).grid(column=0, row=10,
                                                                                                 pady=20)
    CTkButton(master=edit_lights_frame, text='Delete', command=delete_light, font=(CTkFont, 20)).grid(column=2, row=10,
                                                                                                      pady=20)
    edit_lights_frame.grid(row=0, column=1, rowspan=2, sticky=N + S + E + W, padx=8, pady=8)
    # settings frame
    edit_settings_frame = CTkFrame(root)
    edit_settings_frame.grid_columnconfigure(0, minsize=300, weight=1)
    edit_settings_frame.grid_columnconfigure(1, minsize=300, weight=1)
    CTkLabel(edit_settings_frame, text='Edit settings').grid(row=0, column=0, columnspan=2)
    global fps

    def update_label_fps(val, label):
        label.configure(text='Fps:' + str(int(val)))

    fps_label = CTkLabel(edit_settings_frame, text='Fps:' + str(fps), font=(CTkFont, 20))
    fps_label.grid(row=1, column=0, padx=15, pady=15, sticky=W)
    fps_val = customtkinter.IntVar()
    fps_val.set(fps)
    fps_slider = CTkSlider(edit_settings_frame, from_=1, to=60, number_of_steps=60, variable=fps_val,
                           command=lambda x: update_label_fps(x, fps_label))
    fps_slider.grid(row=2, column=0, sticky=E + W, padx=5, pady=15)
    global bar_correction
    black_corection_var = customtkinter.IntVar()
    black_corection_var.set(int(bar_correction))
    black_corection_check = customtkinter.CTkCheckBox(master=edit_settings_frame, text="Black bar correction",
                                                      variable=black_corection_var, onvalue=1, offvalue=2,
                                                      font=(CTkFont, 20))
    black_corection_check.grid(column=0, row=3, padx=15, pady=15, sticky=W)
    global bar_update

    def update_label_bar(val, label):
        label.configure(text='Black bar update interval:' + str(int(val) / 2) + 's')

    black_update_label = CTkLabel(edit_settings_frame, text='Black bar update interval:' + str(bar_update / 2) + 's',
                                  font=(CTkFont, 20))
    black_update_label.grid(row=4, column=0, padx=15, pady=15, sticky=W)
    black_update_var = customtkinter.IntVar()
    black_update_var.set(bar_update)
    black_update_slider = CTkSlider(edit_settings_frame, from_=1, to=10, number_of_steps=9, variable=black_update_var,
                                    command=lambda x: update_label_bar(x, black_update_label))
    black_update_slider.grid(row=5, column=0, sticky=E + W, padx=5, pady=15)

    def save_settings_b():
        global fps
        global bar_update
        global bar_correction
        fps = fps_val.get()
        bar_correction = bool(black_corection_var.get())
        bar_update = black_update_var.get()
        save_settings()

    def reset_fields_settings():
        global fps
        global bar_update
        global bar_correction
        fps_val.set(fps)
        update_label_fps(fps, fps_label)
        black_corection_var.set(int(bar_correction))
        black_update_var.set(bar_update)
        update_label_bar(bar_update, black_update_label)

    CTkButton(master=edit_settings_frame, text='Save settings', command=save_settings_b, font=(CTkFont, 20)).grid(
        column=1, row=10, pady=20)
    CTkButton(master=edit_settings_frame, text='Back', command=lambda: select_frame(status_frame),
              font=(CTkFont, 20)).grid(column=0, row=10, pady=20)
    edit_settings_frame.grid(row=0, column=1, rowspan=2, sticky=N + S + E + W, padx=8, pady=8)
    select_frame(status_frame)
    root.protocol("WM_DELETE_WINDOW", close_main_window)
    threading.Thread(target=update_lights_state).start()
    root.mainloop()


if __name__ == "__main__":
    load_settings()
    main_menu()
