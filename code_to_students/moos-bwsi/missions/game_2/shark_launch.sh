#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Lemon_shark"
V1="New_Caledonia_catshark"
V2="Bristled_lanternshark"
V3="Spined_pygmy_shark"
V4="Cloudy_catshark"
V5="Slender_smooth-hound"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5)
TYPES=("shark" "shark" "shark" "shark" "shark" "shark")
AUV_PORTS=(9301 9302 9303 9304 9305 9306)
AUV_PSHARE=(9401 9402 9403 9404 9405 9406)
START_POS=("x=-11.0,y=405.0,speed=0,depth=5,heading=293" "x=708.0,y=1117.0,speed=0,depth=5,heading=313" "x=-531.0,y=814.0,speed=0,depth=5,heading=278" "x=-1456.0,y=322.0,speed=0,depth=5,heading=151" "x=-966.0,y=579.0,speed=0,depth=5,heading=158" "x=-214.0,y=-957.0,speed=0,depth=5,heading=220")
BHV=("points=format=bowtie,x=-25.73,y=411.25,height=195,wid1=2007,wid2=1204.2,wid3=195,label=Lemon_shark_bwt" "points=zigzag:691.18,1132.69,-171,1178,403,57" "points=zigzag:-543.87,815.81,-30,1894,416,166" "points=format=bowtie,x=-1449.70,y=310.63,height=139,wid1=1189,wid2=713.4,wid3=139,label=Spined_pygmy_shark_bwt" "points=zigzag:-959.63,563.24,-55,1290,265,152" "points=lawnmower:x=-221.71,y=-966.19,degs=-1,width=145,swath=89,height=893,label=Slender_smooth-hound_lwm")

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
