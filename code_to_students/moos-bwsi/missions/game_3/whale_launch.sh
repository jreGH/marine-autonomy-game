#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Striped_dolphin"
V1="Southern_right_whale_dolphin"
V2="Vaquita"
V3="Long-beaked_common_dolphin"
V4="Beluga_whale"
V5="Franciscana"
V6="Atlantic_humpback_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6)
TYPES=("whale" "whale" "whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9304 9305 9306 9307 9308 9309 9310)
AUV_PSHARE=(9404 9405 9406 9407 9408 9409 9410)
START_POS=("x=-249.0,y=-629.0,speed=0,depth=5,heading=47" "x=1368.0,y=1191.0,speed=0,depth=5,heading=322" "x=668.0,y=-1291.0,speed=0,depth=5,heading=198" "x=772.0,y=95.0,speed=0,depth=5,heading=278" "x=1224.0,y=-1169.0,speed=0,depth=5,heading=238" "x=410.0,y=-1420.0,speed=0,depth=5,heading=244" "x=229.0,y=1063.0,speed=0,depth=5,heading=55")
BHV=("polygon=format=ellipse,x=-240.96,y=-621.50,degs=45,minor=284,major=1061,pts=16,label=Striped_dolphin_wpt" "polygon=format=ellipse,x=1353.84,y=1209.12,degs=-148,minor=268,major=822,pts=16,label=Southern_right_whale_dolphin_wpt" "polygon=format=ellipse,x=664.91,y=-1300.51,degs=137,minor=361,major=952,pts=16,label=Vaquita_wpt" "polygon=format=ellipse,x=757.15,y=97.09,degs=-113,minor=450,major=1438,pts=16,label=Long-beaked_common_dolphin_wpt" "polygon=format=ellipse,x=1207.89,y=-1179.07,degs=163,minor=333,major=1041,pts=16,label=Beluga_whale_wpt" "polygon=format=ellipse,x=398.32,y=-1425.70,degs=119,minor=599,major=1456,pts=16,label=Franciscana_wpt" "polygon=format=ellipse,x=238.83,y=1069.88,degs=-135,minor=319,major=1054,pts=16,label=Atlantic_humpback_dolphin_wpt")

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
