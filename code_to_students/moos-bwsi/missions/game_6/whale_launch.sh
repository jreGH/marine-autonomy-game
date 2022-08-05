#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="New_Zealand_dolphin"
V1="Deraniyagalas_Beaked_Whale"
V2="Arnouxs_beaked_whale"
V3="Pygmy_right_whale"
V4="Frasers_dolphin"
V5="Commersons_dolphin"
V6="Melon-headed_whale"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6)
TYPES=("whale" "whale" "whale" "whale" "whale" "whale" "whale")
AUV_PORTS=(9303 9304 9305 9306 9307 9308 9309)
AUV_PSHARE=(9403 9404 9405 9406 9407 9408 9409)
START_POS=("x=319.0,y=1061.0,speed=0,depth=5,heading=165" "x=818.0,y=156.0,speed=0,depth=5,heading=241" "x=531.0,y=917.0,speed=0,depth=5,heading=296" "x=-269.0,y=726.0,speed=0,depth=5,heading=86" "x=-344.0,y=7.0,speed=0,depth=5,heading=80" "x=-1387.0,y=1474.0,speed=0,depth=5,heading=175" "x=426.0,y=1038.0,speed=0,depth=5,heading=151")
BHV=("polygon=format=ellipse,x=324.18,y=1041.68,degs=-134,minor=437,major=874,pts=16,label=New_Zealand_dolphin_wpt" "polygon=format=ellipse,x=805.76,y=149.21,degs=-149,minor=520,major=1440,pts=16,label=Deraniyagalas_Beaked_Whale_wpt" "polygon=format=ellipse,x=512.13,y=926.21,degs=-143,minor=561,major=1229,pts=16,label=Arnouxs_beaked_whale_wpt" "polygon=format=ellipse,x=-257.03,y=726.84,degs=-70,minor=295,major=1010,pts=16,label=Pygmy_right_whale_wpt" "polygon=format=ellipse,x=-320.36,y=11.17,degs=-16,minor=359,major=1080,pts=16,label=Frasers_dolphin_wpt" "polygon=format=ellipse,x=-1385.00,y=1451.09,degs=-29,minor=475,major=1370,pts=16,label=Commersons_dolphin_wpt" "polygon=format=ellipse,x=436.67,y=1018.76,degs=-166,minor=407,major=1103,pts=16,label=Melon-headed_whale_wpt")

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
