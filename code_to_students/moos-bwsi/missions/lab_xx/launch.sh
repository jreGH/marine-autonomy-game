#!/bin/bash -e
#----------------------------------------------------------

#----------------------------------------------------------
#  Part 1: Set Exit actions and declare global var defaults
#----------------------------------------------------------
TIME_WARP=1
GUI="yes"

### Declare all vehicles
VEHICLES=("jellyfish" "otter")
AUV_PORTS=("9001" "9002")
PLATFORM_TYPE=("auv" "kayak")

### Declare all NPCs
NPCS=("whale" "dolphin")
NPC_PORTS=("9201" "9202")
NPC_TYPE=("auv" "auv")


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
for i in ${!VEHICLES[@]}; do
  echo "Launching ${VEHICLES[$i]} MOOS Community. WARP is" $TIME_WARP
  nsplug auv_base.moos ${VEHICLES[$i]}.moos AUV_NAME="${VEHICLES[$i]}" AUV_PORT=${AUV_PORTS[$i]} SHORESIDE_PORT=9000
  pAntler ${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done


for i in ${!NPCS[@]}; do
  echo "Launching ${NPCS[$i]} MOOS Community. WARP is" $TIME_WARP
  nsplug npc_base.moos ${NPCS[$i]}.moos AUV_NAME="${NPCS[$i]}" AUV_PORT=${NPC_PORTS[$i]} SHORESIDE_PORT=9000
  pAntler ${NPCS[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

#echo "Launching $COMMUNITY_A MOOS Community. WARP is" $TIME_WARP
#nsplug auv_base.moos $COMMUNITY_A.moos AUV_NAME="${COMMUNITY_A}" AUV_PORT=9001 SHORESIDE_PORT=9000
#pAntler $COMMUNITY_A.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

#echo "Launching $COMMUNITY_B MOOS Community. WARP is" $TIME_WARP
#nsplug auv_base.moos $COMMUNITY_B.moos AUV_NAME="${COMMUNITY_B}" AUV_PORT=9002 SHORESIDE_PORT=9000
#pAntler $COMMUNITY_B.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
pAntler shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

uMAC -t shoreside.moos
