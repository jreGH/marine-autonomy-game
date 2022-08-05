#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Sea_chub"
V1="Mud_minnow"
V2="Flounder"
V3="John_Dory"
V4="Warty_angler"
V5="North_Pacific_daggertooth"
V6="Common_carp"
V7="Marine_hatchetfish"
V8="Blackchin"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=10.116.0.2
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9312 9313 9314 9315 9316 9317 9318 9319 9320)
AUV_PSHARE=(9412 9413 9414 9415 9416 9417 9418 9419 9420)
START_POS=("x=-653.0,y=-111.0,speed=0,depth=5,heading=35" "x=-841.0,y=-1347.0,speed=0,depth=5,heading=130" "x=-1204.0,y=-747.0,speed=0,depth=5,heading=1" "x=-1002.0,y=417.0,speed=0,depth=5,heading=198" "x=332.0,y=316.0,speed=0,depth=5,heading=334" "x=1438.0,y=-958.0,speed=0,depth=5,heading=187" "x=-891.0,y=-319.0,speed=0,depth=5,heading=96" "x=1026.0,y=1325.0,speed=0,depth=5,heading=337" "x=-1117.0,y=219.0,speed=0,depth=5,heading=349")
BHV=("polygon=radial::x=-645.54,y=-100.35,radius=3,pts=6,label=Sea_chub_loiter" "polygon=radial::x=-829.51,y=-1356.64,radius=3,pts=6,label=Mud_minnow_loiter" "polygon=radial::x=-1203.70,y=-730.00,radius=3,pts=6,label=Flounder_loiter" "polygon=radial::x=-1006.64,y=402.73,radius=3,pts=6,label=John_Dory_loiter" "polygon=radial::x=322.79,y=334.87,radius=3,pts=6,label=Warty_angler_loiter" "polygon=radial::x=1435.68,y=-976.86,radius=3,pts=6,label=North_Pacific_daggertooth_loiter" "polygon=radial::x=-866.14,y=-321.61,radius=3,pts=6,label=Common_carp_loiter" "polygon=radial::x=1017.40,y=1345.25,radius=3,pts=6,label=Marine_hatchetfish_loiter" "polygon=radial::x=-1120.82,y=238.63,radius=3,pts=6,label=Blackchin_loiter")

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
