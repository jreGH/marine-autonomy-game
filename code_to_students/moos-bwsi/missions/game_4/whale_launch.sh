#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Pygmy_sperm_whale"
V1="Grays_beaked_whale"
V2="Tucuxi"
V3="Atlantic_humpback_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3)
TYPES=("whale" "whale" "whale" "whale")
AUV_PORTS=(9303 9304 9305 9306)
AUV_PSHARE=(9403 9404 9405 9406)
START_POS=("x=612.0,y=526.0,speed=0,depth=5,heading=112" "x=-1179.0,y=200.0,speed=0,depth=5,heading=116" "x=808.0,y=28.0,speed=0,depth=5,heading=10" "x=970.0,y=1090.0,speed=0,depth=5,heading=94")
BHV=("polygon=format=ellipse,x=631.47,y=518.13,degs=-97,minor=550,major=1303,pts=16,label=Pygmy_sperm_whale_wpt" "polygon=format=ellipse,x=-1163.72,y=192.55,degs=-6,minor=344,major=1099,pts=16,label=Grays_beaked_whale_wpt" "polygon=format=ellipse,x=810.08,y=39.82,degs=-99,minor=226,major=769,pts=16,label=Tucuxi_wpt" "polygon=format=ellipse,x=985.96,y=1088.88,degs=-126,minor=373,major=897,pts=16,label=Atlantic_humpback_dolphin_wpt")

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
