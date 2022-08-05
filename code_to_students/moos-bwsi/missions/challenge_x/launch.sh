#!/bin/bash -e
#----------------------------------------------------------

#----------------------------------------------------------
#  Part 1: Set Exit actions and declare global var defaults
#----------------------------------------------------------
trap "kill -- -$$" EXIT SIGTERM SIGHUP SIGINT SIGKILL
TIME_WARP=1
COMMUNITY="squid"
GUI="yes"

#----------------------------------------------------------
#  Part 2: Check for and handle command-line arguments
#----------------------------------------------------------
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


#----------------------------------------------------------
#  Part 3: Launch the processes
#----------------------------------------------------------
echo "Launching shoreside  MOOS Community. WARP is" $TIME_WARP
pAntler shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
cat vehicle.bhv challenge/challenge_01.bhv > ${COMMUNITY}.bhv
pAntler $COMMUNITY.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
echo "Launching $COMMUNITY MOOS Community. WARP is" $TIME_WARP

cd challenge
echo "Launching kraken MOOS Community. WARP is" $TIME_WARP
pAntler kraken.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
echo "Launching jaws MOOS Community. WARP is" $TIME_WARP
pAntler jaws.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
cd ..

uMAC -t shoreside.moos
rm ${COMMUNITY}.bhv

