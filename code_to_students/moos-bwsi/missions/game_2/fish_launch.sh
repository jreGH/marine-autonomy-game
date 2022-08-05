#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Redtooth_triggerfish"
V1="Squirrelfish"
V2="Soldierfish"
V3="Scat"
V4="Nibble_fish"
V5="Sardine"
V6="Tubeshoulder"
V7="Javelin"
V8="Ling_cod"
V9="Bat_ray"
V10="Scorpionfish"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=10.116.0.2
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9313 9314 9315 9316 9317 9318 9319 9320 9321 9322 9323)
AUV_PSHARE=(9413 9414 9415 9416 9417 9418 9419 9420 9421 9422 9423)
START_POS=("x=698.0,y=737.0,speed=0,depth=5,heading=313" "x=471.0,y=-894.0,speed=0,depth=5,heading=326" "x=-781.0,y=-481.0,speed=0,depth=5,heading=259" "x=225.0,y=28.0,speed=0,depth=5,heading=144" "x=-1280.0,y=-596.0,speed=0,depth=5,heading=72" "x=-301.0,y=-680.0,speed=0,depth=5,heading=322" "x=-435.0,y=-1323.0,speed=0,depth=5,heading=215" "x=-821.0,y=-964.0,speed=0,depth=5,heading=334" "x=-780.0,y=-736.0,speed=0,depth=5,heading=39" "x=-17.0,y=-465.0,speed=0,depth=5,heading=244" "x=1003.0,y=800.0,speed=0,depth=5,heading=273")
BHV=("polygon=radial::x=683.37,y=750.64,radius=3,pts=6,label=Redtooth_triggerfish_loiter" "polygon=radial::x=459.82,y=-877.42,radius=3,pts=6,label=Squirrelfish_loiter" "polygon=radial::x=-805.54,y=-485.77,radius=3,pts=6,label=Soldierfish_loiter" "polygon=radial::x=239.69,y=7.77,radius=3,pts=6,label=Scat_loiter" "polygon=radial::x=-1257.17,y=-588.58,radius=3,pts=6,label=Nibble_fish_loiter" "polygon=radial::x=-315.78,y=-661.09,radius=3,pts=6,label=Sardine_loiter" "polygon=radial::x=-441.88,y=-1332.83,radius=3,pts=6,label=Tubeshoulder_loiter" "polygon=radial::x=-831.52,y=-942.43,radius=3,pts=6,label=Javelin_loiter" "polygon=radial::x=-768.67,y=-722.01,radius=3,pts=6,label=Ling_cod_loiter" "polygon=radial::x=-27.79,y=-470.26,radius=3,pts=6,label=Bat_ray_loiter" "polygon=radial::x=981.03,y=801.15,radius=3,pts=6,label=Scorpionfish_loiter")

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
