#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Striped_catshark"
V1="Seychelles_carpetshark"
V2="Sharpnose_sevengill_shark"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2)
TYPES=("shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303)
AUV_PSHARE=(9401 9402 9403)
START_POS=("x=455.0,y=-1303.0,speed=0,depth=5,heading=31" "x=649.0,y=1342.0,speed=0,depth=5,heading=277" "x=795.0,y=-1405.0,speed=0,depth=5,heading=46")
BHV=("points=format=bowtie,x=467.36,y=-1282.43,height=58,wid1=1623,wid2=973.8,wid3=58,label=Striped_catshark_bwt" "points=format=bowtie,x=625.18,y=1344.92,height=126,wid1=1284,wid2=770.4,wid3=126,label=Seychelles_carpetshark_bwt" "points=zigzag:809.39,-1391.11,152,2034,241,74")

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
