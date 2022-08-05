#!/bin/bash -e
#----------------------------------------------------------

#----------------------------------------------------------
#  Part 1: Set Exit actions and declare global var defaults
#----------------------------------------------------------
TIME_WARP=1
COMMUNITY_1="jellyfish"
COMMUNITY_2="shoreside"
COMMUNITY_3="otter"
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
echo "Launching $COMMUNITY_1 MOOS Community. WARP is" $TIME_WARP
nsplug -f ${COMMUNITY_1}_base.moos ${COMMUNITY_1}.moos
pAntler $COMMUNITY_1.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

echo "Launching $COMMUNITY_3 MOOS Community. WARP is" $TIME_WARP
nsplug -f ${COMMUNITY_3}_base.moos ${COMMUNITY_3}.moos
pAntler $COMMUNITY_3.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

echo "Launching $COMMUNITY_2 MOOS Community. WARP is" $TIME_WARP
pAntler $COMMUNITY_2.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

uMAC -t $COMMUNITY_2.moos
