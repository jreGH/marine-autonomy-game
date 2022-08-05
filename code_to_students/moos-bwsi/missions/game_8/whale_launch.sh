#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Gervais_beaked_whale"
V1="Rissos_dolphin"
V2="Indo-pacific_beaked_whale"
V3="Tucuxi"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3)
TYPES=("whale" "whale" "whale" "whale")
AUV_PORTS=(9303 9304 9305 9306)
AUV_PSHARE=(9403 9404 9405 9406)
START_POS=("x=-605.0,y=298.0,speed=0,depth=5,heading=196" "x=-808.0,y=-757.0,speed=0,depth=5,heading=236" "x=803.0,y=128.0,speed=0,depth=5,heading=219" "x=-1490.0,y=312.0,speed=0,depth=5,heading=61")
BHV=("polygon=format=ellipse,x=-610.79,y=277.81,degs=-9,minor=635,major=1312,pts=16,label=Gervais_beaked_whale_wpt" "polygon=format=ellipse,x=-827.07,y=-769.86,degs=74,minor=341,major=955,pts=16,label=Rissos_dolphin_wpt" "polygon=format=ellipse,x=787.27,y=108.57,degs=-179,minor=359,major=1343,pts=16,label=Indo-pacific_beaked_whale_wpt" "polygon=format=ellipse,x=-1477.76,y=318.79,degs=-9,minor=499,major=1071,pts=16,label=Tucuxi_wpt")

#----------------------------------------------------------
#  Part 3: Launch the processes
#----------------------------------------------------------
for i in ${!VEHICLES[@]}; do
	echo "Launching ${VEHICLES[$i]} MOOS Community. WARP is" $TIME_WARP
	nsplug whale_base.bhv targ_${VEHICLES[$i]}.bhv AUV_NAME="${VEHICLES[$i]}" \
		AUV_PORT=${AUV_PORTS[$i]} \
		AUV_PSHARE=${AUV_PSHARE[$i]} \
		AUV_TYPE=${TYPES[$i]} \
		START_POS=${START_POS[$i]} \
		WARP=${TIME_WARP} \
		BHV=${BHV[$i]} \
		SHORESIDE_PORT=9000
	nsplug vehicle_base.moos targ_${VEHICLES[$i]}.moos \
		AUV_NAME="${VEHICLES[$i]}" \
		HOSTIP="${HOSTIP}" \
		AUV_PORT=${AUV_PORTS[$i]} \
		AUV_PSHARE=${AUV_PSHARE[$i]} \
		AUV_TYPE=${TYPES[$i]} \
		START_POS=${START_POS[$i]} \
		WARP=${TIME_WARP} \
		MAX_SPEED=8 \
		MAX_DEPTH=100 \
		SHOREIP="${SHOREIP}" \
		SHORESIDE_PORT=9000 \
		SHORESIDE_PSHARE=9200
	pAntler targ_${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
nsplug shoreside_base.moos targ_shoreside.moos WARP=$TIME_WARP SHOREIP=$SHOREIPSHORESIDE_PORT=9000 SHORESIDE_PSHARE=9200
pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
