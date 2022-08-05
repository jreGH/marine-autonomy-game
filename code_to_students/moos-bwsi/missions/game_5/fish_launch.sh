#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Yellow_weaver"
V1="Pirarucu"
V2="Rock_beauty"
V3="Wolf-eel"
V4="Catfish"
V5="Dwarf_gourami"
V6="Freshwater_eel"
V7="Torrent_fish"
V8="Scup"
V9="Gombessa"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9311 9312 9313 9314 9315 9316 9317 9318 9319 9320)
AUV_PSHARE=(9411 9412 9413 9414 9415 9416 9417 9418 9419 9420)
START_POS=("x=-1372.0,y=-1311.0,speed=0,depth=5,heading=62" "x=-630.0,y=-532.0,speed=0,depth=5,heading=223" "x=-980.0,y=-1044.0,speed=0,depth=5,heading=169" "x=-569.0,y=-217.0,speed=0,depth=5,heading=193" "x=321.0,y=-423.0,speed=0,depth=5,heading=26" "x=-908.0,y=422.0,speed=0,depth=5,heading=345" "x=1350.0,y=1467.0,speed=0,depth=5,heading=279" "x=946.0,y=-383.0,speed=0,depth=5,heading=10" "x=-628.0,y=542.0,speed=0,depth=5,heading=218" "x=-419.0,y=8.0,speed=0,depth=5,heading=227")
BHV=("polygon=radial::x=-1354.34,y=-1301.61,radius=3,pts=6,label=Yellow_weaver_loiter" "polygon=radial::x=-642.28,y=-545.16,radius=3,pts=6,label=Pirarucu_loiter" "polygon=radial::x=-976.18,y=-1063.63,radius=3,pts=6,label=Rock_beauty_loiter" "polygon=radial::x=-571.70,y=-228.69,radius=3,pts=6,label=Wolf-eel_loiter" "polygon=radial::x=325.38,y=-414.01,radius=3,pts=6,label=Catfish_loiter" "polygon=radial::x=-914.47,y=446.15,radius=3,pts=6,label=Dwarf_gourami_loiter" "polygon=radial::x=1325.31,y=1470.91,radius=3,pts=6,label=Freshwater_eel_loiter" "polygon=radial::x=949.47,y=-363.30,radius=3,pts=6,label=Torrent_fish_loiter" "polygon=radial::x=-640.93,y=525.45,radius=3,pts=6,label=Scup_loiter" "polygon=radial::x=-435.09,y=-7.00,radius=3,pts=6,label=Gombessa_loiter")

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
