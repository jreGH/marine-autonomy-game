#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Night_shark"
V1="Longnose_velvet_dogfish"
V2="Dwarf_sawtail_catshark"
V3="Mud_catshark"
V4="Western_gulper_shark"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4)
TYPES=("shark" "shark" "shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303 9304 9305)
AUV_PSHARE=(9401 9402 9403 9404 9405)
START_POS=("x=1267.0,y=-1266.0,speed=0,depth=5,heading=42" "x=-1289.0,y=1002.0,speed=0,depth=5,heading=315" "x=1308.0,y=-1377.0,speed=0,depth=5,heading=78" "x=1136.0,y=-70.0,speed=0,depth=5,heading=5" "x=-542.0,y=-535.0,speed=0,depth=5,heading=29")
BHV=("points=zigzag:1283.73,-1247.42,173,2166,416,117" "points=lawnmower:x=-1305.26,y=1018.26,degs=-173,width=121,swath=190,height=1909,label=Longnose_velvet_dogfish_lwm" "points=lawnmower:x=1325.61,y=-1373.26,degs=59,width=136,swath=149,height=1498,label=Dwarf_sawtail_catshark_lwm" "points=zigzag:1137.31,-55.06,152,1962,477,64" "points=lawnmower:x=-534.24,y=-521.01,degs=-65,width=85,swath=153,height=1530,label=Western_gulper_shark_lwm")

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
