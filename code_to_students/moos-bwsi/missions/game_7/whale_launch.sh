#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Striped_dolphin"
V1="Cuviers_beaked_whale"
V2="Northern_minke_whale"
V3="Young_spotted_dolphin"
V4="Short-finned_pilot_whale"
V5="Dalls_porpoise"
V6="Satos_beaked_whale"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6)
TYPES=("whale" "whale" "whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9304 9305 9306 9307 9308 9309 9310)
AUV_PSHARE=(9404 9405 9406 9407 9408 9409 9410)
START_POS=("x=137.0,y=-338.0,speed=0,depth=5,heading=264" "x=683.0,y=-35.0,speed=0,depth=5,heading=62" "x=-542.0,y=-145.0,speed=0,depth=5,heading=352" "x=1372.0,y=1168.0,speed=0,depth=5,heading=241" "x=-1049.0,y=108.0,speed=0,depth=5,heading=106" "x=1470.0,y=752.0,speed=0,depth=5,heading=337" "x=-749.0,y=-324.0,speed=0,depth=5,heading=194")
BHV=("polygon=format=ellipse,x=118.10,y=-339.99,degs=108,minor=426,major=1011,pts=16,label=Striped_dolphin_wpt" "polygon=format=ellipse,x=705.07,y=-23.26,degs=145,minor=477,major=1155,pts=16,label=Cuviers_beaked_whale_wpt" "polygon=format=ellipse,x=-544.51,y=-127.18,degs=53,minor=606,major=1253,pts=16,label=Northern_minke_whale_wpt" "polygon=format=ellipse,x=1356.26,y=1159.27,degs=-134,minor=654,major=1455,pts=16,label=Young_spotted_dolphin_wpt" "polygon=format=ellipse,x=-1029.77,y=102.49,degs=0,minor=351,major=850,pts=16,label=Short-finned_pilot_whale_wpt" "polygon=format=ellipse,x=1461.01,y=773.17,degs=-176,minor=346,major=894,pts=16,label=Dalls_porpoise_wpt" "polygon=format=ellipse,x=-755.05,y=-348.26,degs=2,minor=444,major=1138,pts=16,label=Satos_beaked_whale_wpt")

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
