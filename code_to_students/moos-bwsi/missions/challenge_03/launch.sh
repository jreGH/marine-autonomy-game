#!/bin/bash -e


#----------------------------------------------------------
# Part 1
#----------------------------------------------------------
TIME_WARP=1
GUI="yes"

### Declare all vehicles
V1="Dory"
V2="Harry"
V3="Nemo"
V4="Steve"
HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V1 $V2 $V3 $V4)
TYPES=("dory" "octopus" "nemo" "shark")
AUV_PORTS=("9001" "9002" "9003" "9004")
AUV_PSHARE=("9201" "9202" "9203" "9204")
START_POS=("x=2022,y=2022,speed=0,heading=0,depth=0" "x=-1500,y=-31.80,speed=0,heading=0,depth=0" "x=1000.00,y=-590,speed=0,heading=0,depth=0" "x=400.00,y=-590,speed=0,heading=0,depth=0")
LOITER_POS=("x=2022.00,y=2022.00" "x=-1500.00,y=250.00" "x=1000.0,y=-600", "x=500.0, y=-700.0")

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
	nsplug ${VEHICLES[$i]}_base.moos targ_${VEHICLES[$i]}.moos \
		AUV_NAME="${VEHICLES[$i]}" \
		HOSTIP="${HOSTIP}" \
		AUV_PORT=${AUV_PORTS[$i]} \
		AUV_PSHARE=${AUV_PSHARE[$i]} \
		AUV_TYPE=${TYPES[$i]} \
		WARP=${TIME_WARP} \
		START_POS=${START_POS[$i]} \
		SHOREIP="${SHOREIP}" \
		SHORESIDE_PORT=9000 \
		SHORESIDE_PSHARE=9200
	pAntler targ_${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
nsplug shoreside_base.moos targ_shoreside.moos WARP=${TIME_WARP} SHORESIDE_PSHARE=9200 SHORESIDE_PORT=9000
pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
