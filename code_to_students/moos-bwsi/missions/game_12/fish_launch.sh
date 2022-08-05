#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Ridgehead"
V1="Torrent_catfish"
V2="Sole"
V3="Red_grouper"
V4="Demoiselle"
V5="Goatfish"
V6="Redtooth_triggerfish"
V7="Morwong"
V8="Yellowtail_snapper"
V9="Pirate_perch"
V10="Zebra_pleco"
V11="Albacore"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9310 9311 9312 9313 9314 9315 9316 9317 9318 9319 9320 9321)
AUV_PSHARE=(9410 9411 9412 9413 9414 9415 9416 9417 9418 9419 9420 9421)
START_POS=("x=-650.0,y=1060.0,speed=0,depth=5,heading=188" "x=1273.0,y=-425.0,speed=0,depth=5,heading=186" "x=1202.0,y=-1060.0,speed=0,depth=5,heading=274" "x=88.0,y=773.0,speed=0,depth=5,heading=142" "x=1328.0,y=-161.0,speed=0,depth=5,heading=273" "x=732.0,y=22.0,speed=0,depth=5,heading=45" "x=32.0,y=-1004.0,speed=0,depth=5,heading=114" "x=-406.0,y=1077.0,speed=0,depth=5,heading=299" "x=686.0,y=417.0,speed=0,depth=5,heading=250" "x=-291.0,y=1152.0,speed=0,depth=5,heading=307" "x=-386.0,y=331.0,speed=0,depth=5,heading=222" "x=391.0,y=-695.0,speed=0,depth=5,heading=198")
BHV=("polygon=radial::x=-652.64,y=1041.18,radius=3,pts=6,label=Ridgehead_loiter" "polygon=radial::x=1271.75,y=-436.93,radius=3,pts=6,label=Torrent_catfish_loiter" "polygon=radial::x=1188.03,y=-1059.02,radius=3,pts=6,label=Sole_loiter" "polygon=radial::x=102.78,y=754.09,radius=3,pts=6,label=Red_grouper_loiter" "polygon=radial::x=1317.02,y=-160.42,radius=3,pts=6,label=Demoiselle_loiter" "polygon=radial::x=747.56,y=37.56,radius=3,pts=6,label=Goatfish_loiter" "polygon=radial::x=46.62,y=-1010.51,radius=3,pts=6,label=Redtooth_triggerfish_loiter" "polygon=radial::x=-425.24,y=1087.67,radius=3,pts=6,label=Morwong_loiter" "polygon=radial::x=663.45,y=408.79,radius=3,pts=6,label=Yellowtail_snapper_loiter" "polygon=radial::x=-302.98,y=1161.03,radius=3,pts=6,label=Pirate_perch_loiter" "polygon=radial::x=-400.72,y=314.65,radius=3,pts=6,label=Zebra_pleco_loiter" "polygon=radial::x=384.82,y=-714.02,radius=3,pts=6,label=Albacore_loiter")

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
