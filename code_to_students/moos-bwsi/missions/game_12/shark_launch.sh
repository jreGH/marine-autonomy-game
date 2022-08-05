#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Draughtsboard_shark"
V1="Magnificent_catshark"
V2="White-margin_fin_smooth-hound"
V3="Fat_catshark"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3)
TYPES=("shark" "shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303 9304)
AUV_PSHARE=(9401 9402 9403 9404)
START_POS=("x=1233.0,y=-461.0,speed=0,depth=5,heading=190" "x=732.0,y=-1467.0,speed=0,depth=5,heading=274" "x=-799.0,y=690.0,speed=0,depth=5,heading=303" "x=415.0,y=334.0,speed=0,depth=5,heading=334")
BHV=("points=lawnmower:x=1228.66,y=-485.62,degs=55,width=91,swath=104,height=1043,label=Draughtsboard_shark_lwm" "points=format=bowtie,x=721.03,y=-1466.23,height=119,wid1=2243,wid2=1345.8,wid3=119,label=Magnificent_catshark_bwt" "points=lawnmower:x=-812.42,y=698.71,degs=-177,width=80,swath=170,height=1705,label=White-margin_fin_smooth-hound_lwm" "points=lawnmower:x=406.23,y=351.98,degs=-213,width=167,swath=210,height=2102,label=Fat_catshark_lwm")

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
