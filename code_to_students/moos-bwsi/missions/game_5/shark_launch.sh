#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Horn_shark"
V1="Shortnose_spurdog"
V2="Longfin_catshark"
V3="Creek_whaler"
V4="Northern_river_shark"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4)
TYPES=("shark" "shark" "shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303 9304 9305)
AUV_PSHARE=(9401 9402 9403 9404 9405)
START_POS=("x=129.0,y=213.0,speed=0,depth=5,heading=319" "x=-236.0,y=133.0,speed=0,depth=5,heading=316" "x=1068.0,y=-17.0,speed=0,depth=5,heading=69" "x=1310.0,y=410.0,speed=0,depth=5,heading=133" "x=509.0,y=410.0,speed=0,depth=5,heading=328")
BHV=("points=zigzag:118.50,225.08,-157,1190,260,64" "points=format=bowtie,x=-247.81,y=145.23,height=149,wid1=2045,wid2=1227.0,wid3=149,label=Shortnose_spurdog_bwt" "points=format=bowtie,x=1079.20,y=-12.70,height=147,wid1=846,wid2=507.59999999999997,wid3=147,label=Longfin_catshark_bwt" "points=zigzag:1324.63,396.36,-162,916,169,153" "points=format=bowtie,x=498.40,y=426.96,height=125,wid1=1559,wid2=935.4,wid3=125,label=Northern_river_shark_bwt")

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
