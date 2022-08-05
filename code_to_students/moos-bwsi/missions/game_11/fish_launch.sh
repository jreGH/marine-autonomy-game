#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Black_dragonfish"
V1="Halosaur"
V2="Sea_chub"
V3="Loach_minnow"
V4="Danio"
V5="Shark"
V6="Sturgeon"
V7="Oarfish"
V8="Bluefish"
V9="Threadfin_bream"
V10="Tubeshoulder"
V11="Triplespine"
V12="Bighead_carp"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11 $V12)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9311 9312 9313 9314 9315 9316 9317 9318 9319 9320 9321 9322 9323)
AUV_PSHARE=(9411 9412 9413 9414 9415 9416 9417 9418 9419 9420 9421 9422 9423)
START_POS=("x=-863.0,y=-179.0,speed=0,depth=5,heading=300" "x=-434.0,y=-790.0,speed=0,depth=5,heading=146" "x=67.0,y=518.0,speed=0,depth=5,heading=338" "x=-1457.0,y=-1251.0,speed=0,depth=5,heading=189" "x=1321.0,y=972.0,speed=0,depth=5,heading=325" "x=1128.0,y=140.0,speed=0,depth=5,heading=256" "x=570.0,y=1180.0,speed=0,depth=5,heading=348" "x=-248.0,y=1057.0,speed=0,depth=5,heading=102" "x=1196.0,y=-759.0,speed=0,depth=5,heading=292" "x=1400.0,y=1061.0,speed=0,depth=5,heading=200" "x=-703.0,y=877.0,speed=0,depth=5,heading=151" "x=109.0,y=1345.0,speed=0,depth=5,heading=271" "x=-1294.0,y=-620.0,speed=0,depth=5,heading=147")
BHV=("polygon=radial::x=-883.78,y=-167.00,radius=3,pts=6,label=Black_dragonfish_loiter" "polygon=radial::x=-423.38,y=-805.75,radius=3,pts=6,label=Halosaur_loiter" "polygon=radial::x=58.01,y=540.25,radius=3,pts=6,label=Sea_chub_loiter" "polygon=radial::x=-1460.13,y=-1270.75,radius=3,pts=6,label=Loach_minnow_loiter" "polygon=radial::x=1309.53,y=988.38,radius=3,pts=6,label=Danio_loiter" "polygon=radial::x=1109.56,y=135.40,radius=3,pts=6,label=Shark_loiter" "polygon=radial::x=565.43,y=1201.52,radius=3,pts=6,label=Sturgeon_loiter" "polygon=radial::x=-236.26,y=1054.51,radius=3,pts=6,label=Oarfish_loiter" "polygon=radial::x=1184.87,y=-754.50,radius=3,pts=6,label=Bluefish_loiter" "polygon=radial::x=1395.21,y=1047.84,radius=3,pts=6,label=Threadfin_bream_loiter" "polygon=radial::x=-697.18,y=866.50,radius=3,pts=6,label=Tubeshoulder_loiter" "polygon=radial::x=98.00,y=1345.19,radius=3,pts=6,label=Triplespine_loiter" "polygon=radial::x=-1284.20,y=-635.10,radius=3,pts=6,label=Bighead_carp_loiter")

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
