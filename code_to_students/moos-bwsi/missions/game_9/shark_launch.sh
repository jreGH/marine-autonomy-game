#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Redspotted_catshark"
V1="Starspotted_smooth-hound"
V2="Sicklefin_lemon_shark"
V3="Porbeagle_shark"
V4="Borneo_broadfin_shark"
V5="Necklace_carpetshark"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5)
TYPES=("shark" "shark" "shark" "shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303 9304 9305 9306)
AUV_PSHARE=(9401 9402 9403 9404 9405 9406)
START_POS=("x=-120.0,y=949.0,speed=0,depth=5,heading=274" "x=-877.0,y=-1019.0,speed=0,depth=5,heading=292" "x=712.0,y=-249.0,speed=0,depth=5,heading=252" "x=-182.0,y=1406.0,speed=0,depth=5,heading=41" "x=1158.0,y=-555.0,speed=0,depth=5,heading=300" "x=238.0,y=663.0,speed=0,depth=5,heading=57")
BHV=("points=zigzag:-143.94,950.67,-6,1715,378,165" "points=lawnmower:x=-898.33,y=-1010.38,degs=-31,width=115,swath=132,height=1328,label=Starspotted_smooth-hound_lwm" "points=zigzag:688.22,-256.73,159,1406,264,195" "points=zigzag:-169.53,1420.34,-26,2080,388,50" "points=zigzag:1143.28,-546.50,117,1909,308,73" "points=lawnmower:x=253.10,y=672.80,degs=-213,width=112,swath=169,height=1690,label=Necklace_carpetshark_lwm")

#----------------------------------------------------------
#  Part 3: Launch the processes
#----------------------------------------------------------
for i in ${!VEHICLES[@]}; do
	echo "Launching ${VEHICLES[$i]} MOOS Community. WARP is" $TIME_WARP
	nsplug shark_base.bhv targ_${VEHICLES[$i]}.bhv AUV_NAME="${VEHICLES[$i]}" \
		AUV_PORT=${AUV_PORTS[$i]} \
		AUV_PSHARE=${AUV_PSHARE[$i]} \
		AUV_TYPE=${TYPES[$i]} \
		START_POS=${START_POS[$i]} \
		WARP=${TIME_WARP} \
		MAX_SPEED=18 \
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
		MAX_SPEED=18 \
		MAX_DEPTH=50 \
		SHOREIP="${SHOREIP}" \
		SHORESIDE_PORT=9000 \
		SHORESIDE_PSHARE=9200
	pAntler targ_${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

#echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
#nsplug shoreside_base.moos targ_shoreside.moos WARP=$TIME_WARP SHOREIP=$SHOREIP SHORESIDE_PORT=9000 SHORESIDE_PSHARE=9200
#pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
