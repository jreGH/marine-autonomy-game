#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Trues_beaked_whale"
V1="Northern_bottlenose_whale"
V2="Vaquita"
V3="South_Asian_river_dolphin"
V4="Short-beaked_common_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=10.116.0.2
VEHICLES=($V0 $V1 $V2 $V3 $V4)
TYPES=("whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9307 9308 9309 9310 9311)
AUV_PSHARE=(9407 9408 9409 9410 9411)
START_POS=("x=-1038.0,y=1153.0,speed=0,depth=5,heading=278" "x=1145.0,y=412.0,speed=0,depth=5,heading=301" "x=-6.0,y=585.0,speed=0,depth=5,heading=181" "x=-1442.0,y=-240.0,speed=0,depth=5,heading=43" "x=-1070.0,y=236.0,speed=0,depth=5,heading=132")
BHV=("polygon=format=ellipse,x=-1058.80,y=1155.92,degs=-7,minor=298,major=951,pts=16,label=Trues_beaked_whale_wpt" "polygon=format=ellipse,x=1134.71,y=418.18,degs=-98,minor=543,major=1165,pts=16,label=Northern_bottlenose_whale_wpt" "polygon=format=ellipse,x=-6.35,y=565.00,degs=-75,minor=400,major=869,pts=16,label=Vaquita_wpt" "polygon=format=ellipse,x=-1424.95,y=-221.72,degs=24,minor=451,major=1246,pts=16,label=South_Asian_river_dolphin_wpt" "polygon=format=ellipse,x=-1055.14,y=222.62,degs=-23,minor=412,major=1105,pts=16,label=Short-beaked_common_dolphin_wpt")

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

#echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
#nsplug shoreside_base.moos targ_shoreside.moos WARP=$TIME_WARP SHORESIDE_PORT=9000 SHORESIDE_PSHARE=9200
#pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
