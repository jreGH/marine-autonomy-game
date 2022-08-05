#!/bin/bash -e
#----------------------------------------------------------

#----------------------------------------------------------
#  Part 1: Set Exit actions and declare global var defaults
#----------------------------------------------------------
TIME_WARP=1
VEHICLES=("jellyfish" "otter")
AUV_PORTS=("9001" "9002")
SHORESIDE_PORT="9000"

COMMUNITY_2="shoreside"
GUI="yes"

#----------------------------------------------------------
#  Part 2: Check for and handle command-line arguments
#----------------------------------------------------------
SHORT=h,w:
LONG=help,nogui,warp:
OPTS=$(getopt --options $SHORT --longoptions $LONG -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1; fi

eval set -- "$OPTS"

while true;
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
			shift
			;;

		-w | --warp )
			TIME_WARP=$2
			shift 2
			;;

		-- )
			shift;
			break
			;;

		*)
			echo "Unexpected option: $1"
			break
			;;
	esac
done

#----------------------------------------------------------
#  Part 3: Launch the processes
#----------------------------------------------------------
for i in ${!VEHICLES[@]};do
	echo "Launching ${VEHICLES[$i]} MOOS Community. WARP is" $TIME_WARP
	nsplug auv_base.moos ${VEHICLES[$i]}.moos AUV_NAME=${VEHICLES[$i]} AUV_PORT=${AUV_PORTS[$i]} SHORESIDE_PORT=${SHORESIDE_PORT}
	pAntler ${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

echo "Launching $COMMUNITY_2 MOOS Community. WARP is" $TIME_WARP
pAntler $COMMUNITY_2.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

uMAC -t $COMMUNITY_2.moos
