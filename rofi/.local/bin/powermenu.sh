#!/usr/bin/env bash
rofi_command="rofi -theme $HOME/.config/rofi/powermenu.rasi"

uptime=$(uptime -p | sed -e 's/up //g')

# Options
if [[ "$DIR" == "powermenus" ]]; then
	shutdown=""
	reboot=""
	lock=""
	suspend=""
	logout=""
	ddir="$HOME/.config/rofi/config"
else
	# Buttons
	layout=`cat $HOME/.config/rofi/powermenu.rasi | grep BUTTON | cut -d'=' -f2 | tr -d '[:blank:],*/'`
	if [[ "$layout" == "TRUE" ]]; then
 		shutdown="襤"
		reboot=""
		logout=""
	else
		shutdown="襤Shutdown"
		reboot="ﰇ Restart"
		logout=" Logout"
	fi
	ddir="$HOME/.config/rofi"
fi

# Variable passed to rofi
options="$logout\n$reboot\n$shutdown"

chosen="$(echo -e "$options" | $rofi_command -p "UP - $uptime" -dmenu -selected-row 0)"
case $chosen in
    $shutdown)
		systemctl poweroff
		;;
    $reboot)
		systemctl reboot
		;;
    $logout)
			bspc quit
        ;;
esac


