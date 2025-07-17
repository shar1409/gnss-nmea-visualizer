import ttkbootstrap as ttk
from tkinter import filedialog, scrolledtext
from tkintermapview import TkinterMapView
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import threading
import time
import math

# Globals
coord, altitude, time_data, nmea_lines, cycle = [], [], [], [], []
second_groups = []
current_index = 0


def nmea_to_dec_lat(coord_str, direction):
    if not coord_str or not direction:
        return 0.0
    degrees = int(coord_str[:2])
    minutes = float(coord_str[2:]) / 60
    decimal = degrees + minutes
    return -decimal if direction == 'S' else decimal


def nmea_to_dec_long(coord_str, direction):
    if not coord_str or not direction:
        return 0.0
    degrees = int(coord_str[:3])
    minutes = float(coord_str[3:]) / 60
    decimal = degrees + minutes
    return -decimal if direction == 'W' else decimal


def extract_gpgsv_group(lines, start_index):
    parts = lines[start_index].split(',')
    try:
        total_msgs = int(parts[1])
    except:
        return [], start_index + 1
    return lines[start_index:start_index + total_msgs], start_index + total_msgs


def browse_file():
    global coord, altitude, time_data, cycle, current_index, nmea_lines, second_groups
    coord.clear()
    altitude.clear()
    time_data.clear()
    cycle.clear()
    nmea_lines.clear()
    second_groups.clear()
    current_index = 0

    path = filedialog.askopenfilename(filetypes=[("NMEA Files", "*.nmea *.txt")])
    if not path:
        return

    lines = []
    with open(path, 'r') as file:
        for line in file:
            stripped_line = line.strip()
            if stripped_line:
                lines.append(stripped_line)
    nmea_lines.extend(lines)
    

    raw_lines = []
    current_block = []
    current_time = None

    for line in nmea_lines:
        if line.startswith("$GPGGA") or line.startswith("$GPRMC"):
            parts = line.split(',')
            if len(parts) > 1 and parts[1]:
                line_time = parts[1][:6]
                if line_time != current_time:
                    if current_block:
                        second_groups.append(current_block)
                    current_block = []
                    current_time = line_time
        current_block.append(line)

        if line.startswith("$GPGGA"):
            parts = line.split(",")
            if len(parts) > 9:
                lat, lat_dir, lon, lon_dir, alt = parts[2], parts[3], parts[4], parts[5], parts[9]
                if lat and lon and lat_dir and lon_dir and alt:
                    coord.append((nmea_to_dec_lat(lat, lat_dir), nmea_to_dec_long(lon, lon_dir)))
                    altitude.append(float(alt))

        if line.startswith("$GPGSV"):
            raw_lines.append(line)

    if current_block:
        second_groups.append(current_block)

    i = 0
    while i < len(raw_lines):
        group, i = extract_gpgsv_group(raw_lines, i)
        if group:
            cycle.append(group)

    threading.Thread(target=update_loop, daemon=True).start()


def update_loop():
    global current_index
    while current_index < len(coord):
        update_all()
        time.sleep(1)
        current_index += 1


def update_all():
    update_nmea_display()
    update_map()
    update_coords_display()
    update_charts()


def update_nmea_display():
    text_display.config(state='normal')
    if current_index < len(second_groups):
        for line in second_groups[current_index]:
            text_display.insert('end', line + '\n')
        text_display.insert('end', '\n')
        text_display.see('end')
    text_display.config(state='disabled')


def update_map():
    if current_index >= len(coord): return
    lat, lon = coord[current_index]
    map_widget.set_position(lat, lon)
    map_widget.set_zoom(15)
    map_widget.delete_all_marker()
    map_widget.set_marker(lat, lon)


def update_coords_display():
    if current_index >= len(coord): return
    lat, lon = coord[current_index]
    alt = altitude[current_index]
    latitude_label.config(text=f"Latitude: {lat:.6f}")
    longitude_label.config(text=f"Longitude: {lon:.6f}")
    altitude_label.config(text=f"Altitude: {alt:.2f} m")


def refresh_data():
    text_display.config(state='normal')
    text_display.delete(1.0, 'end')
    text_display.config(state='disabled')


def update_charts():
    if current_index >= len(cycle): return
    group = cycle[current_index]
    prn_snr_map = {}
    azimuths, elevations = [], []
    for line in group:
        parts = line.split(',')
        for i in range(4, len(parts) - 3, 4):
            try:
                prn = parts[i]
                elev = float(parts[i + 1])
                azim = float(parts[i + 2])
                snr = parts[i + 3]
                if prn and snr.isdigit():
                    prn_snr_map['G' + prn] = int(snr)
                if 0 <= azim <= 360 and 0 <= elev <= 90:
                    azimuths.append(math.radians(azim))
                    elevations.append(90 - elev)
            except:
                continue

    ax_snr.clear()
    x = list(prn_snr_map.keys())
    y = list(prn_snr_map.values())
    bars = ax_snr.bar(range(len(x)), y, color='#444444')
    ax_snr.set_xticks(range(len(x)))
    ax_snr.set_xticklabels(x, rotation=90)
    ax_snr.set_title("SNR")
    ax_snr.set_ylim(0, 60)
    for bar in bars:
        height = bar.get_height()
        ax_snr.text(bar.get_x() + bar.get_width() / 2, height + 1, f"{height}", ha='center', fontsize=7)

    ax_az.clear()
    ax_az.set_theta_zero_location('N')
    ax_az.set_theta_direction(-1)
    ax_az.set_rlim(0, 90)
    ax_az.grid(True)
    if azimuths:
        ax_az.scatter(azimuths, elevations, c='red', s=40, edgecolors='black')
    ax_az.set_title("Azimuth Skyplot", fontsize=9)
    canvas_snr.draw()
    canvas_az.draw()


# App setup
app = ttk.Window(themename="flatly")
app.title("GNSS Viewer")
app.geometry("1300x700")
app.configure(background="#dbe7ed")

style = ttk.Style()
style.configure("BoldBlack.TLabelframe.Label", font=("Arial", 10, "bold"), foreground="black", background="#dbe7ed")
style.configure("BoldBlack.TLabelframe", background="#dbe7ed", borderwidth=2, relief="groove")
style.configure("BG.TFrame", background="#dbe7ed")

left = ttk.Frame(app, style="BG.TFrame")
left.pack(side='left', fill='both', expand=True)
right = ttk.Frame(app, padding=10, style="BG.TFrame")
right.pack(side='right', fill='y')

frame_top = ttk.Frame(left, style="BG.TFrame")
frame_top.pack(fill='both', expand=True)
frame_bot = ttk.Frame(left, style="BG.TFrame")
frame_bot.pack(fill='both', expand=True)

map_frame = ttk.LabelFrame(frame_top, text="World Position", padding=5, style="BoldBlack.TLabelframe")
map_frame.pack(side='left', fill='both', expand=True, padx=3, pady=3)
map_widget = TkinterMapView(map_frame, width=400, height=200, corner_radius=0)
map_widget.pack(fill='both', expand=True)
map_widget.set_position(20, 80)
map_widget.set_zoom(5)

snr_frame = ttk.LabelFrame(frame_top, text="Satellite Level, C/N₀ (dB-Hz)", padding=5, style="BoldBlack.TLabelframe")
snr_frame.pack(side='right', fill='both', expand=True, padx=3, pady=3)
fig_snr, ax_snr = plt.subplots(figsize=(4, 3))
fig_snr.patch.set_facecolor("lightgray")
canvas_snr = FigureCanvasTkAgg(fig_snr, master=snr_frame)
canvas_snr.get_tk_widget().pack(fill='both', expand=True)

az_frame = ttk.LabelFrame(frame_bot, text="Satellite Position", padding=5, style="BoldBlack.TLabelframe")
az_frame.pack(side='left', fill='both', expand=True, padx=3, pady=3)
fig_az, ax_az = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(4, 3))
canvas_az = FigureCanvasTkAgg(fig_az, master=az_frame)
canvas_az.get_tk_widget().pack(fill='both', expand=True)

info_frame = ttk.LabelFrame(frame_bot, text="GNSS Data", padding=5, style="BoldBlack.TLabelframe")
info_frame.pack(side='right', fill='both', expand=True, padx=3, pady=3)
latitude_label = ttk.Label(info_frame, text="Latitude: N/A", font=("Courier New", 10))
latitude_label.pack(anchor='w', pady=2)
longitude_label = ttk.Label(info_frame, text="Longitude: N/A", font=("Courier New", 10))
longitude_label.pack(anchor='w', pady=2)
altitude_label = ttk.Label(info_frame, text="Altitude: N/A", font=("Courier New", 10))
altitude_label.pack(anchor='w', pady=2)

ttk.Button(right, text="Browse File", command=browse_file).pack(pady=5, fill='x')
ttk.Button(right, text="Refresh", command=refresh_data).pack(pady=5, fill='x')

label = ttk.Label(right, text="NMEA Data", font=("Arial", 11, "bold"))
label.pack(pady=5)
text_display = scrolledtext.ScrolledText(right, wrap='word', height=40, font=("Courier New", 9), bg="#f4f4f4")
text_display.pack(fill='both', expand=True)
text_display.config(state='disabled')

app.mainloop()
