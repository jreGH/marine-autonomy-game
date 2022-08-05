#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Elasmobranch"
V1="Righteye_flounder"
V2="Harelip_sucker"
V3="Taimen"
V4="Bristlenose_catfish"
V5="Lanternfish"
V6="Desert_pupfish"
V7="Flagfin"
V8="Madtom"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9307 9308 9309 9310 9311 9312 9313 9314 9315)
AUV_PSHARE=(9407 9408 9409 9410 9411 9412 9413 9414 9415)
START_POS=("x=-979.0,y=1159.0,speed=0,depth=5,heading=305" "x=1122.0,y=920.0,speed=0,depth=5,heading=354" "x=1353.0,y=504.0,speed=0,depth=5,heading=4" "x=-1079.0,y=-945.0,speed=0,depth=5,heading=181" "x=-131.0,y=175.0,speed=0,depth=5,heading=155" "x=-912.0,y=-67.0,speed=0,depth=5,heading=35" "x=-124.0,y=-1472.0,speed=0,depth=5,heading=335" "x=389.0,y=121.0,speed=0,depth=5,heading=126" "x=274.0,y=-755.0,speed=0,depth=5,heading=207")
BHV=("polygon=radial::x=-988.83,y=1165.88,radius=3,pts=6,label=Elasmobranch_loiter" "polygon=radial::x=1119.80,y=940.88,radius=3,pts=6,label=Righteye_flounder_loiter" "polygon=radial::x=1354.53,y=525.95,radius=3,pts=6,label=Harelip_sucker_loiter" "polygon=radial::x=-1079.44,y=-970.00,radius=3,pts=6,label=Taimen_loiter" "polygon=radial::x=-126.77,y=165.94,radius=3,pts=6,label=Bristlenose_catfish_loiter" "polygon=radial::x=-905.69,y=-57.99,radius=3,pts=6,label=Lanternfish_loiter" "polygon=radial::x=-132.45,y=-1453.87,radius=3,pts=6,label=Desert_pupfish_loiter" "polygon=radial::x=406.80,y=108.07,radius=3,pts=6,label=Flagfin_loiter" "polygon=radial::x=264.47,y=-773.71,radius=3,pts=6,label=Madtom_loiter")

#----------------------------------------------------------
#  Part 3: Launch the processes
#----------------------------------------------------------
for i in ${!VEHICLES[@]}; do
	echo "Launching ${VEHICLES[$i]} MOOS Community. WARP is" $TIME_WARP
	nsplug fish_base.bhv targ_${VEHICLES[$i]}.bhv AUV_NAME="${VEHICLES[$i]}" \
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
		MAX_SPEED=3 \
		MAX_DEPTH=300 \
		SHOREIP="${SHOREIP}" \
		SHORESIDE_PORT=9000 \
		SHORESIDE_PSHARE=9200
	pAntler targ_${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
done

#echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP
#nsplug shoreside_base.moos targ_shoreside.moos WARP=$TIME_WARP SHORESIDE_PORT=9000 SHORESIDE_PSHARE=9200
#pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
