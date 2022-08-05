#!/bin/bash -e
#----------------------------------------------------------

#----------------------------------------------------------
#  Part 1: Set Exit actions and declare global var defaults
#----------------------------------------------------------
TIME_WARP=1
GUI="yes"

### Declare all vehicles
# TODO: figure out better way to handle V1, V2
V1="dolphin"
V2="whale"
VNAMES=$V1:$V2
VEHICLES=($V1 $V2)
TYPES=("kayak" "kayak")
AUV_PORTS=("9001" "9002")
AUV_PSHARE=("9201" "9202")
START_POS=("170,-80,270" "-30,-80,90")        
LOITER_POS=("x=0,y=-95" "x=125,y=-65")
 
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
  nsplug ${VEHICLES[$i]}_base.bhv targ_${VEHICLES[$i]}.bhv AUV_NAME="${VEHICLES[$i]}" \
	  AUV_PORT=${AUV_PORTS[$i]} \
	  AUV_PSHARE=${AUV_PSHARE[$i]} \
	  AUV_TYPE=${TYPES[$i]} \
	  START_POS=${START_POS[$i]} \
	  LOITER_POS=${LOITER_POS[$i]} \
	  WARP=${TIME_WARP} \
	  SHORESIDE_PORT=9000
  nsplug vehicle_base.moos targ_${VEHICLES[$i]}.moos \
	  AUV_NAME="${VEHICLES[$i]}" \
	  AUV_PORT=${AUV_PORTS[$i]} \
	  AUV_PSHARE=${AUV_PSHARE[$i]} \
	  AUV_TYPE=${TYPES[$i]} \
	  WARP=${TIME_WARP} \
	  START_POS=${START_POS[$i]} \
	  SHORESIDE_PORT=9000 \
	  SHORESIDE_PSHARE=9200
  pAntler targ_${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
nsplug shoreside_base.moos targ_shoreside.moos AUV_NAMES=${VNAMES} WARP=${TIME_WARP} SHORESIDE_PSHARE=9200 SHORESIDE_PORT=9000
pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &

uMAC -t targ_shoreside.moos
