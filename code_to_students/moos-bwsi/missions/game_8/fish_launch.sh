#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Temperate_ocean-bass"
V1="Pancake_batfish"
V2="Sand_dab"
V3="Goatfish"
V4="Sharksucker"
V5="Pirarucu"
V6="North_American_darter"
V7="Gurnard"
V8="Warmouth"
V9="Lake_whitefish"
V10="Batfish"
V11="Fingerfish"
V12="Yellowfin_tuna"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11 $V12)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9307 9308 9309 9310 9311 9312 9313 9314 9315 9316 9317 9318 9319)
AUV_PSHARE=(9407 9408 9409 9410 9411 9412 9413 9414 9415 9416 9417 9418 9419)
START_POS=("x=-1270.0,y=-1378.0,speed=0,depth=5,heading=84" "x=123.0,y=-623.0,speed=0,depth=5,heading=40" "x=-994.0,y=-763.0,speed=0,depth=5,heading=115" "x=533.0,y=-1330.0,speed=0,depth=5,heading=121" "x=111.0,y=1271.0,speed=0,depth=5,heading=132" "x=-907.0,y=-80.0,speed=0,depth=5,heading=314" "x=-1464.0,y=723.0,speed=0,depth=5,heading=67" "x=610.0,y=-388.0,speed=0,depth=5,heading=322" "x=-680.0,y=428.0,speed=0,depth=5,heading=292" "x=730.0,y=-1115.0,speed=0,depth=5,heading=276" "x=1445.0,y=505.0,speed=0,depth=5,heading=258" "x=920.0,y=867.0,speed=0,depth=5,heading=187" "x=1154.0,y=802.0,speed=0,depth=5,heading=141")
BHV=("polygon=radial::x=-1248.12,y=-1375.70,radius=3,pts=6,label=Temperate_ocean-bass_loiter" "polygon=radial::x=134.57,y=-609.21,radius=3,pts=6,label=Pancake_batfish_loiter" "polygon=radial::x=-978.59,y=-770.18,radius=3,pts=6,label=Sand_dab_loiter" "polygon=radial::x=545.00,y=-1337.21,radius=3,pts=6,label=Goatfish_loiter" "polygon=radial::x=124.38,y=1258.96,radius=3,pts=6,label=Sharksucker_loiter" "polygon=radial::x=-917.79,y=-69.58,radius=3,pts=6,label=Pirarucu_loiter" "polygon=radial::x=-1446.51,y=730.42,radius=3,pts=6,label=North_American_darter_loiter" "polygon=radial::x=595.22,y=-369.09,radius=3,pts=6,label=Gurnard_loiter" "polygon=radial::x=-694.83,y=433.99,radius=3,pts=6,label=Warmouth_loiter" "polygon=radial::x=710.11,y=-1112.91,radius=3,pts=6,label=Lake_whitefish_loiter" "polygon=radial::x=1421.52,y=500.01,radius=3,pts=6,label=Batfish_loiter" "polygon=radial::x=917.68,y=848.14,radius=3,pts=6,label=Fingerfish_loiter" "polygon=radial::x=1167.85,y=784.90,radius=3,pts=6,label=Yellowfin_tuna_loiter")

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
#nsplug shoreside_base.moos targ_shoreside.moos WARP=$TIME_WARP SHOREIP=$SHOREIP SHORESIDE_PORT=9000 SHORESIDE_PSHARE=9200
#pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &
