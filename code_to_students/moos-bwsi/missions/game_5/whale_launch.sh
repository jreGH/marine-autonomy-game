#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Frasers_dolphin"
V1="Melon-headed_whale"
V2="Brydes_whale"
V3="Rough-toothed_dolphin"
V4="Australian_snubfin_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4)
TYPES=("whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9306 9307 9308 9309 9310)
AUV_PSHARE=(9406 9407 9408 9409 9410)
START_POS=("x=720.0,y=-1363.0,speed=0,depth=5,heading=163" "x=-648.0,y=747.0,speed=0,depth=5,heading=37" "x=-1068.0,y=-1484.0,speed=0,depth=5,heading=342" "x=-948.0,y=251.0,speed=0,depth=5,heading=221" "x=851.0,y=-896.0,speed=0,depth=5,heading=277")
BHV=("polygon=format=ellipse,x=725.85,y=-1382.13,degs=176,minor=679,major=1497,pts=16,label=Frasers_dolphin_wpt" "polygon=format=ellipse,x=-637.77,y=760.58,degs=-19,minor=228,major=869,pts=16,label=Melon-headed_whale_wpt" "polygon=format=ellipse,x=-1073.25,y=-1467.83,degs=44,minor=432,major=965,pts=16,label=Brydes_whale_wpt" "polygon=format=ellipse,x=-961.78,y=235.15,degs=-27,minor=239,major=928,pts=16,label=Rough-toothed_dolphin_wpt" "polygon=format=ellipse,x=832.14,y=-893.68,degs=103,minor=351,major=915,pts=16,label=Australian_snubfin_dolphin_wpt")

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
