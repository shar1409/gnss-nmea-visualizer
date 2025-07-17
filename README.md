# 🛰️ GNSS NMEA Data Visualizer

A real-time GNSS (Global Navigation Satellite System) data visualizer built during my internship at **Navyan Technology**. The tool processes `.nmea` files, extracts and visualizes key satellite navigation parameters using Python GUI and plotting libraries.

## 📌 Features

- ✅ Parses NMEA sentences like **GPGGA** and **GPGSV**
- ✅ Displays live coordinates (Latitude, Longitude, Altitude)
- ✅ Plots:
  - 🌐 Real-time position on OpenStreetMap
  - 📡 Skyplot for satellite azimuth and elevation
  - 📶 SNR (Signal-to-Noise Ratio) bar chart
- ✅ Scrollable NMEA raw message display
- ✅ GUI built with **Tkinter** and enhanced using **ttkbootstrap**
- ✅ Auto-refreshes and updates all panels simultaneously

## 🔧 Technologies Used

- Python 3.10+
- Tkinter
- ttkbootstrap
- matplotlib
- tkintermapview

## 📁 Directory Structure

┣ 📜 final_gui.py # Main application script
┣ 📜 requirements.txt # Python dependencies
┣ 📜 README.md # Project documentation
┣ 📁 sample_data/ # Sample .nmea file(s)
