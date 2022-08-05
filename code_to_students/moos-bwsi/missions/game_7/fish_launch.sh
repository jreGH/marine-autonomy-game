#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Antarctic_cod"
V1="Sharksucker"
V2="New_Zealand_sand_diver"
V3="Duckbill_eel"
V4="Desert_pupfish"
V5="Glass_catfish"
V6="Escolar"
V7="Armored_searobin"
V8="Orangespine_unicorn_fish"
V9="Livebearer"
V10="Coho_salmon"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9311 9312 9313 9314 9315 9316 9317 9318 9319 9320 9321)
AUV_PSHARE=(9411 9412 9413 9414 9415 9416 9417 9418 9419 9420 9421)
START_POS=("x=1423.0,y=-488.0,speed=0,depth=5,heading=352" "x=-1435.0,y=588.0,speed=0,depth=5,heading=109" "x=-577.0,y=11.0,speed=0,depth=5,heading=55" "x=-465.0,y=138.0,speed=0,depth=5,heading=229" "x=890.0,y=-57.0,speed=0,depth=5,heading=54" "x=32.0,y=-1077.0,speed=0,depth=5,heading=15" "x=816.0,y=-352.0,speed=0,depth=5,heading=265" "x=483.0,y=-123.0,speed=0,depth=5,heading=266" "x=-679.0,y=122.0,speed=0,depth=5,heading=190" "x=1240.0,y=-721.0,speed=0,depth=5,heading=157" "x=320.0,y=706.0,speed=0,depth=5,heading=37")
BHV=("polygon=radial::x=1421.19,y=-475.13,radius=3,pts=6,label=Antarctic_cod_loiter" "polygon=radial::x=-1417.04,y=581.81,radius=3,pts=6,label=Sharksucker_loiter" "polygon=radial::x=-568.81,y=16.74,radius=3,pts=6,label=New_Zealand_sand_diver_loiter" "polygon=radial::x=-481.60,y=123.57,radius=3,pts=6,label=Duckbill_eel_loiter" "polygon=radial::x=903.75,y=-47.01,radius=3,pts=6,label=Desert_pupfish_loiter" "polygon=radial::x=34.85,y=-1066.37,radius=3,pts=6,label=Glass_catfish_loiter" "polygon=radial::x=803.05,y=-353.13,radius=3,pts=6,label=Escolar_loiter" "polygon=radial::x=463.05,y=-124.40,radius=3,pts=6,label=Armored_searobin_loiter" "polygon=radial::x=-682.82,y=100.33,radius=3,pts=6,label=Orangespine_unicorn_fish_loiter" "polygon=radial::x=1247.03,y=-737.57,radius=3,pts=6,label=Livebearer_loiter" "polygon=radial::x=326.62,y=714.78,radius=3,pts=6,label=Coho_salmon_loiter")

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
