#----------------------------------------------------------
TIME_WARP=1

### Declare all vehicles
V0="Australasian_salmon_"
V1="Muskellunge"
V2="Rockfish"
V3="Pufferfish"
V4="Sea_bass"
V5="Old_World_knifefish"
V6="Hairtail"
V7="Roach"
V8="Cutlassfish"
V9="Ilish/Hilsha"
V10="Nase"
V11="Nurseryfish"

HOSTIP=`hostname -I | awk '{print $3}'`
SHOREIP=$HOSTIP
VEHICLES=($V0 $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11)
TYPES=("fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish" "fish")
AUV_PORTS=(9309 9310 9311 9312 9313 9314 9315 9316 9317 9318 9319 9320)
AUV_PSHARE=(9409 9410 9411 9412 9413 9414 9415 9416 9417 9418 9419 9420)
START_POS=("x=566.0,y=-1147.0,speed=0,depth=5,heading=281" "x=1492.0,y=-1113.0,speed=0,depth=5,heading=133" "x=801.0,y=1019.0,speed=0,depth=5,heading=91" "x=-1326.0,y=1160.0,speed=0,depth=5,heading=236" "x=741.0,y=808.0,speed=0,depth=5,heading=201" "x=-1262.0,y=896.0,speed=0,depth=5,heading=176" "x=849.0,y=338.0,speed=0,depth=5,heading=287" "x=-378.0,y=106.0,speed=0,depth=5,heading=184" "x=104.0,y=-452.0,speed=0,depth=5,heading=26" "x=1064.0,y=-523.0,speed=0,depth=5,heading=230" "x=87.0,y=-212.0,speed=0,depth=5,heading=227" "x=-232.0,y=-417.0,speed=0,depth=5,heading=44")
BHV=("polygon=radial::x=541.46,y=-1142.23,radius=3,pts=6,label=Australasian_salmon__loiter" "polygon=radial::x=1506.63,y=-1126.64,radius=3,pts=6,label=Muskellunge_loiter" "polygon=radial::x=815.00,y=1018.76,radius=3,pts=6,label=Rockfish_loiter" "polygon=radial::x=-1345.07,y=1147.14,radius=3,pts=6,label=Pufferfish_loiter" "polygon=radial::x=737.06,y=797.73,radius=3,pts=6,label=Sea_bass_loiter" "polygon=radial::x=-1261.23,y=885.03,radius=3,pts=6,label=Old_World_knifefish_loiter" "polygon=radial::x=827.96,y=344.43,radius=3,pts=6,label=Hairtail_loiter" "polygon=radial::x=-379.40,y=86.05,radius=3,pts=6,label=Roach_loiter" "polygon=radial::x=110.14,y=-439.42,radius=3,pts=6,label=Cutlassfish_loiter" "polygon=radial::x=1049.45,y=-535.21,radius=3,pts=6,label=Ilish/Hilsha_loiter" "polygon=radial::x=73.10,y=-224.96,radius=3,pts=6,label=Nase_loiter" "polygon=radial::x=-220.19,y=-404.77,radius=3,pts=6,label=Nurseryfish_loiter")

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
