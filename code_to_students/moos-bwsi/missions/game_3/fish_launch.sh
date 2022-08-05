#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Denticle_herring"
V1="Ruffe"
V2="Sand_lance"
V3="Scaly_dragonfish"
V4="Sandfish"
V5="Skipjack_tuna"
V6="Fierasfer"
V7="Sheatfish"
V8="Needlefish"
V9="Dab"
V10="Banjo"
V11="Flier"
V12="Discus"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11 $V12)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9311 9312 9313 9314 9315 9316 9317 9318 9319 9320 9321 9322 9323)
AUV_PSHARE=(9411 9412 9413 9414 9415 9416 9417 9418 9419 9420 9421 9422 9423)
START_POS=("x=1004.0,y=800.0,speed=0,depth=5,heading=194" "x=700.0,y=95.0,speed=0,depth=5,heading=343" "x=-1478.0,y=-848.0,speed=0,depth=5,heading=115" "x=-1169.0,y=1292.0,speed=0,depth=5,heading=208" "x=379.0,y=-1281.0,speed=0,depth=5,heading=54" "x=-523.0,y=-807.0,speed=0,depth=5,heading=353" "x=995.0,y=-78.0,speed=0,depth=5,heading=164" "x=-352.0,y=1016.0,speed=0,depth=5,heading=155" "x=-753.0,y=-230.0,speed=0,depth=5,heading=266" "x=1158.0,y=907.0,speed=0,depth=5,heading=200" "x=-425.0,y=-580.0,speed=0,depth=5,heading=216" "x=31.0,y=1318.0,speed=0,depth=5,heading=218" "x=688.0,y=-299.0,speed=0,depth=5,heading=175")
BHV=("polygon=radial::x=998.44,y=777.68,radius=3,pts=6,label=Denticle_herring_loiter" "polygon=radial::x=695.61,y=109.34,radius=3,pts=6,label=Ruffe_loiter" "polygon=radial::x=-1465.31,y=-853.92,radius=3,pts=6,label=Sand_lance_loiter" "polygon=radial::x=-1175.10,y=1280.52,radius=3,pts=6,label=Scaly_dragonfish_loiter" "polygon=radial::x=389.52,y=-1273.36,radius=3,pts=6,label=Sandfish_loiter" "polygon=radial::x=-524.22,y=-797.07,radius=3,pts=6,label=Skipjack_tuna_loiter" "polygon=radial::x=999.96,y=-95.30,radius=3,pts=6,label=Fierasfer_loiter" "polygon=radial::x=-345.24,y=1001.50,radius=3,pts=6,label=Sheatfish_loiter" "polygon=radial::x=-762.98,y=-230.70,radius=3,pts=6,label=Needlefish_loiter" "polygon=radial::x=1153.21,y=893.84,radius=3,pts=6,label=Dab_loiter" "polygon=radial::x=-431.47,y=-588.90,radius=3,pts=6,label=Banjo_loiter" "polygon=radial::x=18.69,y=1302.24,radius=3,pts=6,label=Flier_loiter" "polygon=radial::x=689.39,y=-314.94,radius=3,pts=6,label=Discus_loiter")

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
