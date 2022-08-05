#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Springfish"
V1="Glassfish"
V2="Pencil_catfish"
V3="Largemouth_bass"
V4="Humuhumunukunukuapuaa"
V5="Cownose_ray"
V6="Devario"
V7="Paradise_fish"
V8="Barracudina"
V9="Naked-back_knifefish"
V10="Swampfish"
V11="Trevally"
V12="Stonefish"
V13="Channel_bass"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11 $V12 $V13)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9310 9311 9312 9313 9314 9315 9316 9317 9318 9319 9320 9321 9322 9323)
AUV_PSHARE=(9410 9411 9412 9413 9414 9415 9416 9417 9418 9419 9420 9421 9422 9423)
START_POS=("x=1183.0,y=-1152.0,speed=0,depth=5,heading=100" "x=888.0,y=686.0,speed=0,depth=5,heading=188" "x=-1318.0,y=-284.0,speed=0,depth=5,heading=266" "x=-1488.0,y=888.0,speed=0,depth=5,heading=66" "x=-1437.0,y=791.0,speed=0,depth=5,heading=65" "x=-595.0,y=-1134.0,speed=0,depth=5,heading=42" "x=273.0,y=-387.0,speed=0,depth=5,heading=280" "x=-1323.0,y=805.0,speed=0,depth=5,heading=51" "x=1462.0,y=-327.0,speed=0,depth=5,heading=188" "x=1201.0,y=-401.0,speed=0,depth=5,heading=6" "x=-1057.0,y=1216.0,speed=0,depth=5,heading=130" "x=572.0,y=-1283.0,speed=0,depth=5,heading=209" "x=1169.0,y=467.0,speed=0,depth=5,heading=171" "x=-831.0,y=-1358.0,speed=0,depth=5,heading=229")
BHV=("polygon=radial::x=1201.71,y=-1155.30,radius=3,pts=6,label=Springfish_loiter" "polygon=radial::x=884.94,y=664.21,radius=3,pts=6,label=Glassfish_loiter" "polygon=radial::x=-1340.94,y=-285.60,radius=3,pts=6,label=Pencil_catfish_loiter" "polygon=radial::x=-1477.95,y=892.47,radius=3,pts=6,label=Largemouth_bass_loiter" "polygon=radial::x=-1417.97,y=799.87,radius=3,pts=6,label=Humuhumunukunukuapuaa_loiter" "polygon=radial::x=-578.94,y=-1116.16,radius=3,pts=6,label=Cownose_ray_loiter" "polygon=radial::x=253.30,y=-383.53,radius=3,pts=6,label=Devario_loiter" "polygon=radial::x=-1304.35,y=820.10,radius=3,pts=6,label=Paradise_fish_loiter" "polygon=radial::x=1459.91,y=-341.85,radius=3,pts=6,label=Barracudina_loiter" "polygon=radial::x=1203.40,y=-378.13,radius=3,pts=6,label=Naked-back_knifefish_loiter" "polygon=radial::x=-1043.21,y=1204.43,radius=3,pts=6,label=Swampfish_loiter" "polygon=radial::x=563.76,y=-1297.87,radius=3,pts=6,label=Trevally_loiter" "polygon=radial::x=1171.82,y=449.22,radius=3,pts=6,label=Stonefish_loiter" "polygon=radial::x=-849.87,y=-1374.40,radius=3,pts=6,label=Channel_bass_loiter")

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
