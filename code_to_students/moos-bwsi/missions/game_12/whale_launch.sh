#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Narrow-ridged_finless_porpoise"
V1="Sowerbys_beaked_whale"
V2="Indo-Pacific_bottlenose_dolphin"
V3="Frasers_dolphin"
V4="Chilean_dolphin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4)
TYPES=("whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9305 9306 9307 9308 9309)
AUV_PSHARE=(9405 9406 9407 9408 9409)
START_POS=("x=1407.0,y=-746.0,speed=0,depth=5,heading=149" "x=-24.0,y=-1211.0,speed=0,depth=5,heading=61" "x=126.0,y=954.0,speed=0,depth=5,heading=109" "x=-401.0,y=-506.0,speed=0,depth=5,heading=15" "x=-757.0,y=-848.0,speed=0,depth=5,heading=237")
BHV=("polygon=format=ellipse,x=1417.30,y=-763.14,degs=100,minor=296,major=1119,pts=16,label=Narrow-ridged_finless_porpoise_wpt" "polygon=format=ellipse,x=-12.63,y=-1204.70,degs=16,minor=236,major=763,pts=16,label=Sowerbys_beaked_whale_wpt" "polygon=format=ellipse,x=141.13,y=948.79,degs=-126,minor=567,major=1185,pts=16,label=Indo-Pacific_bottlenose_dolphin_wpt" "polygon=format=ellipse,x=-398.15,y=-495.37,degs=37,minor=376,major=870,pts=16,label=Frasers_dolphin_wpt" "polygon=format=ellipse,x=-777.97,y=-861.62,degs=20,minor=274,major=768,pts=16,label=Chilean_dolphin_wpt")

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
