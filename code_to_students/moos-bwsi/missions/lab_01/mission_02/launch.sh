#!/bin/bash -e
COMMUNITY="leatherback"

#-------------------------------------------------------
#  Part 1: Check for and handle command-line arguments
#-------------------------------------------------------
SHORT=h,w:
LONG=help,nogui,warp:
OPTS=$(getopt --options $SHORT --longoptions $LONG)

eval set -- "$OPTS"

while :
do
	case "$1" in
		-h | --help )
			echo "./launch.sh <OPTIONS>"
			echo "-w <#> or --warp <#> is the warp factor"
			echo "--nogui turns off the GUI"
			echo "-h or --help prints this message"
			exit 2
			;;

		--nogui )
			GUI="no"
			shift 1
			;;

		-w | --warp )
			TIME_WARP="$2"
			shift 2
			;;

		-- )
			shift;
			break
			;;

		*)
			echo "Unexpected option: $1"
			;;
	esac
done

#-------------------------------------------------------
#  Part 2: Launch the processes
#-------------------------------------------------------
printf "Launching the %s MOOS Community (WARP=%s) \n"  $COMMUNITY $TIME_WARP
pAntler $COMMUNITY.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

uMAC $COMMUNITY.moos

printf "Killing all processes ... \n"
kill %1 
printf "Done killing processes.   \n"

