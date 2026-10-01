#!/usr/bin/env bash
# Run under dbus-run-session on the recording display.
set -euo pipefail
export DISPLAY=:94
export XDG_CURRENT_DESKTOP=XFCE
export XDG_SESSION_DESKTOP=xfce
export PYTHONDONTWRITEBYTECODE=1
export PATH=/admin/boxman-venv/bin:/usr/local/bin:/usr/bin:/bin
xfconfd=/usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd
"$xfconfd" &
sleep 1
xfconf-query -c xfwm4 -p /general/use_compositing -n -t bool -s false
xfconf-query -c xfce4-desktop -p /desktop-icons/style -n -t int -s 0
xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorscreen/workspace0/image-style -n -t int -s 0
xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitorscreen/workspace0/color-style -n -t int -s 0
gsettings set org.xfce.mousepad.preferences.view use-default-monospace-font false
gsettings set org.xfce.mousepad.preferences.view font-name 'DejaVu Sans Mono 13'
gsettings set org.xfce.mousepad.preferences.view word-wrap true
gsettings set org.xfce.mousepad.state.window width 790
gsettings set org.xfce.mousepad.state.window height 770
gsettings set org.xfce.mousepad.state.window left 580
gsettings set org.xfce.mousepad.state.window top 85
gsettings set org.gtk.Settings.FileChooser startup-mode cwd
gsettings set org.gtk.Settings.FileChooser last-folder-uri 'file:///admin/packer-tutorial'
gsettings set org.gtk.Settings.FileChooser show-hidden false
gsettings set org.xfce.mousepad.preferences.window recent-menu-items 0
xset s off
xset -dpms || true
xfsettingsd --no-daemon &
xfwm4 --replace &
xfdesktop &
xfce4-panel &
wait
