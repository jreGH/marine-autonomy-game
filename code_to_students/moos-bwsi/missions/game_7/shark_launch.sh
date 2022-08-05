#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Dark_shyshark"
V1="Whitespotted_bamboo_shark"
V2="Caribbean_lanternshark"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2)
TYPES=("shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303)
AUV_PSHARE=(9401 9402 9403)
START_POS=("x=1318.0,y=237.0,speed=0,depth=5,heading=261" "x=-542.0,y=-1256.0,speed=0,depth=5,heading=204" "x=-1495.0,y=-277.0,speed=0,depth=5,heading=12")
BHV=("points=zigzag:1306.15,235.12,-126,2132,432,136" "points=lawnmower:x=-547.69,y=-1268.79,degs=-43,width=71,swath=187,height=1876,label=Whitespotted_bamboo_shark_lwm" "points=format=bowtie,x=-1492.30,y=-264.28,height=107,wid1=899,wid2=539.4,wid3=107,label=Caribbean_lanternshark_bwt")

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
