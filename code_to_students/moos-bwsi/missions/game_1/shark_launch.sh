#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Crested_bullhead_shark"
V1="Australian_grey_smooth-hound"
V2="Dark_freckled_catshark"
V3="Longnose_velvet_dogfish"
V4="African_frilled_shark"
V5="Roughback_catshark"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5)
TYPES=("shark" "shark" "shark" "shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303 9304 9305 9306)
AUV_PSHARE=(9401 9402 9403 9404 9405 9406)
START_POS=("x=1381.0,y=640.0,speed=0,depth=5,heading=216" "x=434.0,y=616.0,speed=0,depth=5,heading=1" "x=399.0,y=-730.0,speed=0,depth=5,heading=215" "x=-196.0,y=1295.0,speed=0,depth=5,heading=9" "x=478.0,y=-726.0,speed=0,depth=5,heading=246" "x=498.0,y=-710.0,speed=0,depth=5,heading=1")
BHV=("points=zigzag:1366.89,620.58,-137,783,477,170" "points=format=bowtie,x=434.30,y=633.00,height=95,wid1=1766,wid2=1059.6,wid3=95,label=Australian_grey_smooth-hound_bwt" "points=lawnmower:x=385.81,y=-748.84,degs=65,width=198,swath=179,height=1790,label=Dark_freckled_catshark_lwm" "points=zigzag:-193.34,1311.79,-63,1062,131,172" "points=format=bowtie,x=456.99,y=-735.35,height=90,wid1=1088,wid2=652.8,wid3=90,label=African_frilled_shark_bwt" "points=format=bowtie,x=498.28,y=-694.00,height=159,wid1=1014,wid2=608.4,wid3=159,label=Roughback_catshark_bwt")

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
		MAX_SPEED=12 \
		MAX_DEPTH=50 \
		SHOREIP="${SHOREIP}" \
		SHORESIDE_PORT=9000 \
		SHORESIDE_PSHARE=9200
	pAntler targ_${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

#echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
#nsplug shoreside_base.moos targ_shoreside.moos WARP=$TIME_WARP SHOREIP=$SHOREIP SHORESIDE_PORT=9000 SHORESIDE_PSHARE=9200
#pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
