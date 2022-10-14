#!/usr/bin/env bash

# Terminate already running bar instances
# If all your bars have ipc enabled, you can use 
# polybar-msg cmd quit
# Otherwise you can use the nuclear option:
pkill polybar

# Launch bar1 and bar2
echo "---" | tee -a /tmp/polybar1.log /tmp/polybar2.log
polybar --config=~/.config/polybar/bspwm.ini bspwm 2>&1 | tee -a /tmp/polybar1.log & disown
polybar --config=~/.config/polybar/xwindow.ini xwindow 2>&1 | tee -a /tmp/polybar1.log & disown
polybar --config=~/.config/polybar/window.ini window 2>&1 | tee -a /tmp/polybar1.log & disown
polybar --config=~/.config/polybar/system.ini system 2>&1 | tee -a /tmp/polybar1.log & disown

echo "Bars launched..."
