#!/bin/bash

set -e

export DISPLAY=:1

echo "[start] Launching virtual framebuffer..."
Xvfb :1 -screen 0 1024x768x16 &
sleep 2

echo "[start] Starting XFCE..."
dbus-launch startxfce4 &
sleep 3

echo "[start] Starting x11vnc..."
x11vnc -display :1 -nopw -forever -shared -bg
sleep 1

echo "[start] Starting websockify..."
websockify --web=/usr/share/novnc/ 6080 localhost:5901
