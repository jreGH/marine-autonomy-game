#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Franciscana"
V1="Atlantic_humpback_dolphin"
V2="Rices_whale"
V3="Atlantic_spotted_dolphin"
V4="Bowhead_whale"
V5="Blainvilles_beaked_whale"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5)
TYPES=("whale" "whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9303 9304 9305 9306 9307 9308)
AUV_PSHARE=(9403 9404 9405 9406 9407 9408)
START_POS=("x=223.0,y=815.0,speed=0,depth=5,heading=107" "x=673.0,y=-557.0,speed=0,depth=5,heading=317" "x=659.0,y=685.0,speed=0,depth=5,heading=318" "x=-862.0,y=-1019.0,speed=0,depth=5,heading=59" "x=1199.0,y=402.0,speed=0,depth=5,heading=322" "x=-789.0,y=-1451.0,speed=0,depth=5,heading=200")
BHV=("polygon=format=ellipse,x=237.34,y=810.61,degs=-95,minor=300,major=778,pts=16,label=Franciscana_wpt" "polygon=format=ellipse,x=665.50,y=-548.96,degs=97,minor=599,major=1381,pts=16,label=Atlantic_humpback_dolphin_wpt" "polygon=format=ellipse,x=652.31,y=692.43,degs=-179,minor=289,major=1129,pts=16,label=Rices_whale_wpt" "polygon=format=ellipse,x=-849.14,y=-1011.27,degs=90,minor=613,major=1303,pts=16,label=Atlantic_spotted_dolphin_wpt" "polygon=format=ellipse,x=1185.46,y=419.34,degs=-110,minor=476,major=1295,pts=16,label=Bowhead_whale_wpt" "polygon=format=ellipse,x=-794.13,y=-1465.10,degs=67,minor=334,major=963,pts=16,label=Blainvilles_beaked_whale_wpt")

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
