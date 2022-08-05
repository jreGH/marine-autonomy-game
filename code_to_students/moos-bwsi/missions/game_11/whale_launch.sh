#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Common_bottlenose_dolphin"
V1="Long-finned_pilot_whale"
V2="Short-beaked_common_dolphin"
V3="Hectors_dolphin"
V4="New_Zealand_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4)
TYPES=("whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9306 9307 9308 9309 9310)
AUV_PSHARE=(9406 9407 9408 9409 9410)
START_POS=("x=100.0,y=393.0,speed=0,depth=5,heading=181" "x=1048.0,y=-758.0,speed=0,depth=5,heading=243" "x=676.0,y=1413.0,speed=0,depth=5,heading=334" "x=-1203.0,y=1185.0,speed=0,depth=5,heading=16" "x=-365.0,y=-393.0,speed=0,depth=5,heading=241")
BHV=("polygon=format=ellipse,x=99.67,y=374.00,degs=-178,minor=323,major=764,pts=16,label=Common_bottlenose_dolphin_wpt" "polygon=format=ellipse,x=1037.31,y=-763.45,degs=179,minor=512,major=1063,pts=16,label=Long-finned_pilot_whale_wpt" "polygon=format=ellipse,x=670.30,y=1424.68,degs=-154,minor=332,major=1286,pts=16,label=Short-beaked_common_dolphin_wpt" "polygon=format=ellipse,x=-1199.14,y=1198.46,degs=-48,minor=275,major=775,pts=16,label=Hectors_dolphin_wpt" "polygon=format=ellipse,x=-381.62,y=-402.21,degs=40,minor=585,major=1244,pts=16,label=New_Zealand_dolphin_wpt")

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
