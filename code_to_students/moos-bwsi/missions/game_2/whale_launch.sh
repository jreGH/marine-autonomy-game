#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Guiana_dolphin"
V1="Humpback_whale"
V2="Melon-headed_whale"
V3="Atlantic_white-sided_dolphin"
V4="Common_minke_whale"
V5="Irrawaddy_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=10.116.0.2
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5)
TYPES=("whale" "whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9307 9308 9309 9310 9311 9312)
AUV_PSHARE=(9407 9408 9409 9410 9411 9412)
START_POS=("x=271.0,y=258.0,speed=0,depth=5,heading=105" "x=1244.0,y=1292.0,speed=0,depth=5,heading=166" "x=1327.0,y=819.0,speed=0,depth=5,heading=191" "x=-596.0,y=-622.0,speed=0,depth=5,heading=36" "x=-505.0,y=1446.0,speed=0,depth=5,heading=196" "x=938.0,y=198.0,speed=0,depth=5,heading=9")
BHV=("polygon=format=ellipse,x=293.22,y=252.05,degs=-180,minor=317,major=876,pts=16,label=Guiana_dolphin_wpt" "polygon=format=ellipse,x=1248.35,y=1274.53,degs=-175,minor=589,major=1416,pts=16,label=Humpback_whale_wpt" "polygon=format=ellipse,x=1322.23,y=794.46,degs=-143,minor=416,major=1200,pts=16,label=Melon-headed_whale_wpt" "polygon=format=ellipse,x=-586.60,y=-609.06,degs=71,minor=371,major=833,pts=16,label=Atlantic_white-sided_dolphin_wpt" "polygon=format=ellipse,x=-508.58,y=1433.50,degs=-68,minor=419,major=1305,pts=16,label=Common_minke_whale_wpt" "polygon=format=ellipse,x=939.88,y=209.85,degs=-111,minor=223,major=881,pts=16,label=Irrawaddy_dolphin_wpt")

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
