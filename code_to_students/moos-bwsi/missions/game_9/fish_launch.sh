#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Luderick"
V1="Billfish"
V2="Jewelfish"
V3="Knifejaw"
V4="Lamprey"
V5="Blackfish"
V6="Spanish_mackerel"
V7="Spottail_pinfish"
V8="Redhorse_sucker"
V9="Treefish"
V10="Suckermouth_armored_catfish"
V11="Powen"
V12="Stonefish"
V13="Beardfish"
V14="Tilefish"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11 $V12 $V13 $V14)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9312 9313 9314 9315 9316 9317 9318 9319 9320 9321 9322 9323 9324 9325 9326)
AUV_PSHARE=(9412 9413 9414 9415 9416 9417 9418 9419 9420 9421 9422 9423 9424 9425 9426)
START_POS=("x=-571.0,y=177.0,speed=0,depth=5,heading=264" "x=-311.0,y=954.0,speed=0,depth=5,heading=62" "x=665.0,y=-299.0,speed=0,depth=5,heading=118" "x=623.0,y=-519.0,speed=0,depth=5,heading=107" "x=880.0,y=-649.0,speed=0,depth=5,heading=312" "x=19.0,y=1262.0,speed=0,depth=5,heading=47" "x=224.0,y=1378.0,speed=0,depth=5,heading=86" "x=-392.0,y=1264.0,speed=0,depth=5,heading=149" "x=-767.0,y=-1409.0,speed=0,depth=5,heading=278" "x=-767.0,y=-1231.0,speed=0,depth=5,heading=294" "x=999.0,y=348.0,speed=0,depth=5,heading=103" "x=-1318.0,y=885.0,speed=0,depth=5,heading=340" "x=-756.0,y=-906.0,speed=0,depth=5,heading=109" "x=-427.0,y=160.0,speed=0,depth=5,heading=35" "x=1197.0,y=704.0,speed=0,depth=5,heading=46")
BHV=("polygon=radial::x=-588.90,y=175.12,radius=3,pts=6,label=Luderick_loiter" "polygon=radial::x=-292.46,y=963.86,radius=3,pts=6,label=Billfish_loiter" "polygon=radial::x=682.66,y=-308.39,radius=3,pts=6,label=Jewelfish_loiter" "polygon=radial::x=643.08,y=-525.14,radius=3,pts=6,label=Knifejaw_loiter" "polygon=radial::x=869.60,y=-639.63,radius=3,pts=6,label=Lamprey_loiter" "polygon=radial::x=26.31,y=1268.82,radius=3,pts=6,label=Blackfish_loiter" "polygon=radial::x=239.96,y=1379.12,radius=3,pts=6,label=Spanish_mackerel_loiter" "polygon=radial::x=-384.27,y=1251.14,radius=3,pts=6,label=Spottail_pinfish_loiter" "polygon=radial::x=-779.87,y=-1407.19,radius=3,pts=6,label=Redhorse_sucker_loiter" "polygon=radial::x=-780.70,y=-1224.90,radius=3,pts=6,label=Treefish_loiter" "polygon=radial::x=1017.51,y=343.73,radius=3,pts=6,label=Suckermouth_armored_catfish_loiter" "polygon=radial::x=-1323.47,y=900.04,radius=3,pts=6,label=Powen_loiter" "polygon=radial::x=-736.14,y=-912.84,radius=3,pts=6,label=Stonefish_loiter" "polygon=radial::x=-421.26,y=168.19,radius=3,pts=6,label=Beardfish_loiter" "polygon=radial::x=1214.26,y=720.67,radius=3,pts=6,label=Tilefish_loiter")

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
