import numpy as np
#import matplotlib.pyplot as plt
import random

def animal_names():
    animals = ['Anglerfish','BarreleyeFish','BelugaWhale','BioluminescentOctopus']
    animals.append('BlueGlaucus')
    animals.append('BlueWhale')
    animals.append('Blue-ringedOctopus')
    animals.append('BonnetheadShark')
    animals.append('BottlenoseDolphin')
    animals.append('BoxJellyfish')

    animals.append('ChristmasTreeWorm')
    animals.append('Clownfish')
    animals.append('CookieCutterShark')

    animals.append('Dugong')
    animals.append('DumboOctopus')

    animals.append('FrilledShark')

    animals.append('GhostShark')
    animals.append('GiantIsopod')
    animals.append('GlassOctopus')
    animals.append('GoblinShark')
    animals.append('GranrojoJellyfish')
    animals.append('GreatAuk')
    animals.append('GreenTurtle')

    animals.append('Lanternshark')
    animals.append('LeafySeaDragon')
    animals.append('LeopardShark')
    animals.append('Lizardfish')

    animals.append('Megalodon')
    animals.append('MegamouthShark')
    animals.append('MimicOctopus')

    animals.append('Narwhal')
    animals.append('Needlefish')
    animals.append('NurseShark')

    animals.append('OpenBrainCoral')
    animals.append('Orca')

    animals.append('Parrotfish')
    animals.append('Piranha')
    animals.append('Pufferfish')

    animals.append('RainbowShark')
    animals.append('RedJamaicanCrab')
    animals.append('RedSeaWhip')

    animals.append('Sailfish')
    animals.append('SalmonShark') 
    animals.append('SeaAngel')
    animals.append('SeaBream')
    animals.append('SeaBunny')
    animals.append('SeaButterfly')
    animals.append('SeaHare')
    animals.append('SeaLice')
    animals.append('SeaLily')
    animals.append('SeaNettle')
    animals.append('SeaPig')
    animals.append('SeaRobin')
    animals.append('SeaSheep')
    animals.append('SeaSpider')
    animals.append('SeaTrout')
    animals.append('SpermWhale')
    animals.append('Starfish')
    animals.append('Stargazer')
    animals.append('Swordfish')

    animals.append('TigerShark')

    animals.append('VampireSquid')
    animals.append('Vaquita')


#BEARDED SEAL,BLUE WHALE,BOWHEAD WHALE,CALIFORNIA SEA LION
#FALSE KILLER WHALE,FIN WHALE,GRAY SEAL,GRAY WHALE
#GUADALUPE FUR SEAL,HARBOR SEAL,HARP SEAL,HAWAIIAN MONK SEAL,HOURGLASS DOLPHIN
#HUMPBACK WHALE,JUAN FERNANDEZ FUR SEAL,LEOPARD SEAL,LONG-FINNED PILOT WHALE
#MARINE OTTER,MINKE WHALE,NORTH ATLANTIC RIGHT WHALE
#PANTROPICAL SPOTTED DOLPHIN,POLAR BEAR,RINGED SEAL
#RISSO’S DOLPHIN,SEA OTTER,SHORT-BEAKED COMMON DOLPHIN
#SOUTHERN ELEPHANT SEAL,SPERM WHALE,SPINNER DOLPHIN
#STELLER SEA LION,VAQUITA,WALRUS,WEST INDIAN MANATEE

    return animals


  

def make_launch_file(vehicle_names):

    comment = '#----------------------------------------------------------\n'

    with open('launch.sh', 'wt') as f:
        f.write('#!/bin/bash -e\n')
        f.write('\n\n')
        f.write(comment)
        f.write('# Part 1\n')
        f.write(comment)
        f.write('TIME_WARP=1\n')
        f.write('GUI="yes"\n')
        f.write('\n')
        f.write('### Declare all vehicles\n')
        for i, name in enumerate(vehicle_names):
            f.write(f'V{i+1}="{name}"\n')
        
        f.write('VNAMES=$V1')
        for i in range(1,len(vehicle_names)):
            f.write(f':$V{i+1}')

        f.write('\n')

        f.write('VEHICLES=($V1')
        for i in range(1,len(vehicle_names)):
            f.write(f' $V{i+1}')
        f.write(')\n')
        
        auv_type = 'kayak'
        f.write(f'TYPES=("{auv_type}"')
        for i in range(1,len(vehicle_names)):
            f.write(f' "{auv_type}"')
        f.write(')\n')

        auv_port = 9001
        f.write(f'AUV_PORTS=("{auv_port}"')
        for i in range(1,len(vehicle_names)):
            auv_port = auv_port + 1
            f.write(f' "{auv_port}"')
        f.write(')\n')

        auv_pshare = 9201
        f.write(f'AUV_PSHARE=("{auv_pshare}"')
        for i in range(1,len(vehicle_names)):
            auv_pshare = auv_pshare + 1
            f.write(f' "{auv_pshare}"')
        f.write(')\n')

        x = random.uniform(-250,250)
        y = random.uniform(-250,250)
        hd = 0
        dp = 0
        f.write(f'START_POS=("x={x:.2f},y={y:.2f},speed=0,heading={hd},depth={dp}"')
        for i in range(1,len(vehicle_names)):
            x = random.uniform(-250,250)
            y = random.uniform(-250,250)
            f.write(f' "x={x:.2f},y={y:.2f},speed=0,heading={hd},depth={dp}"')
        f.write(')\n')

        x = -250
        y = 250
        f.write(f'LOITER_POS=("x={x:.2f},y={y:.2f}"')
        for i in range(1,len(vehicle_names)):
            x = x + 55
            if x > 250:
                x = -250
                y = y - 50
            hd = np.mod(hd+22.5, 360)
            f.write(f' "x={x:.2f},y={y:.2f}"')
        f.write(')\n')

        f.write('\n')
        f.write(comment)
        f.write('#  Part 2: Check for and handle command-line arguments\n')
        f.write(comment)
        f.write('SHORT=h,w:\n')
        f.write('LONG=help,nogui,warp:\n')
        f.write('OPTS=$(getopt --options $SHORT --longoptions $LONG -- "$@")\n')

        f.write('if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1; fi\n\n')

        f.write('eval set -- "$OPTS"\n\n')

        f.write('while true;\n')
        f.write('do\n')
        f.write('\tcase "$1" in\n')
        f.write('\t\t-h | --help )\n')
        f.write('\t\t\techo "./launch.sh <OPTIONS>"\n')
        f.write('\t\t\techo "-w <#> or --warp <#> is the warp factor"\n')
        f.write('\t\techo "--nogui turns off the GUI"\n')
        f.write('\t\t\techo "-h or --help prints this message"\n')
        f.write('\t\t\texit 2\n')
        f.write('\t\t\t;;\n')

        f.write('\t\t--nogui )\n')
        f.write('\t\t\tGUI="no"\n')
        f.write('\t\t\tshift\n')
        f.write('\t\t\t;;\n')

        f.write('\t\t-w | --warp )\n')
        f.write('\t\t\tTIME_WARP=$2\n')
        f.write('\t\t\tshift 2\n')
        f.write('\t\t\t;;\n')

        f.write('\t\t-- )\n')
        f.write('\t\t\tshift;\n')
        f.write('\t\t\tbreak\n')
        f.write('\t\t\t;;\n')

        f.write('\t\t*)\n')
        f.write('\t\t\techo "Unexpected option: $1"\n')
        f.write('\t\t\tbreak\n')
        f.write('\t\t\t;;\n')
        f.write('\tesac\n')
        f.write('done\n\n')

        f.write(comment)
        f.write('#  Part 3: Launch the processes\n')
        f.write(comment)
        f.write('for i in ${!VEHICLES[@]}; do\n')
        f.write('\techo "Launching ${VEHICLES[$i]} MOOS Community. WARP is" $TIME_WARP\n')
        f.write('\tnsplug vehicle_base.bhv targ_${VEHICLES[$i]}.bhv AUV_NAME="${VEHICLES[$i]}" \\\n')
        f.write('\t\tAUV_PORT=${AUV_PORTS[$i]} \\\n')
        f.write('\t\tAUV_PSHARE=${AUV_PSHARE[$i]} \\\n')
        f.write('\t\tAUV_TYPE=${TYPES[$i]} \\\n')
        f.write('\t\tSTART_POS=${START_POS[$i]} \\\n')
        f.write('\t\tLOITER_POS=${LOITER_POS[$i]} \\\n')
        f.write('\t\tWARP=${TIME_WARP} \\\n')
        f.write('\t\tSHORESIDE_PORT=9000\n')
        f.write('\tnsplug vehicle_base.moos targ_${VEHICLES[$i]}.moos \\\n')
        f.write('\t\tAUV_NAME="${VEHICLES[$i]}" \\\n')
        f.write('\t\tAUV_PORT=${AUV_PORTS[$i]} \\\n')
        f.write('\t\tAUV_PSHARE=${AUV_PSHARE[$i]} \\\n')
        f.write('\t\tAUV_TYPE=${TYPES[$i]} \\\n')
        f.write('\t\tWARP=${TIME_WARP} \\\n')
        f.write('\t\tSTART_POS=${START_POS[$i]} \\\n')
        f.write('\t\tSHORESIDE_PORT=9000 \\\n')
        f.write('\t\tSHORESIDE_PSHARE=9200\n')
        f.write('\tpAntler targ_${VEHICLES[$i]}.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &\n')
        f.write('done\n\n')

        f.write('echo "Launching shoreside MOOS Community, WARP is" $TIME_WARP\n')
        f.write('nsplug shoreside_base.moos targ_shoreside.moos AUV_NAMES=${VNAMES} WARP=${TIME_WARP} SHORESIDE_PSHARE=9200 SHORESIDE_PORT=9000\n')
        f.write('pAntler targ_shoreside.moos --MOOSTimeWarp=$TIME_WARP >& /dev/null &\n')


if __name__ == "__main__":
    NAMES = animal_names()
    N = 4
    random.shuffle(NAMES)
    make_launch_file(NAMES[:N])
