#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Amazon_River_dolphin"
V1="Frasers_dolphin"
V2="Melon-headed_whale"
V3="Southern_right_whale_dolphin"
V4="Rissos_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4)
TYPES=("whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9307 9308 9309 9310 9311)
AUV_PSHARE=(9407 9408 9409 9410 9411)
START_POS=("x=586.0,y=-1067.0,speed=0,depth=5,heading=26" "x=366.0,y=-361.0,speed=0,depth=5,heading=61" "x=-816.0,y=565.0,speed=0,depth=5,heading=169" "x=-1370.0,y=-516.0,speed=0,depth=5,heading=261" "x=-334.0,y=-275.0,speed=0,depth=5,heading=358")
BHV=("polygon=format=ellipse,x=592.58,y=-1053.52,degs=124,minor=735,major=1475,pts=16,label=Amazon_River_dolphin_wpt" "polygon=format=ellipse,x=377.37,y=-354.70,degs=144,minor=694,major=1482,pts=16,label=Frasers_dolphin_wpt" "polygon=format=ellipse,x=-813.90,y=554.20,degs=-44,minor=468,major=1056,pts=16,label=Melon-headed_whale_wpt" "polygon=format=ellipse,x=-1385.80,y=-518.50,degs=12,minor=357,major=1232,pts=16,label=Southern_right_whale_dolphin_wpt" "polygon=format=ellipse,x=-334.49,y=-261.01,degs=54,minor=260,major=811,pts=16,label=Rissos_dolphin_wpt")

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
