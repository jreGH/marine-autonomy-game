#!/bin/bash 

VERBOSE=""

#-------------------------------------------------
# Part 1: Command line options
#-------------------------------------------------
SHORT=h,v
LONG=help,verbose
OPTS=$(getopt --options $SHORT --longoptions $LONG)

eval set -- "$OPTS"

while :
do
	case "$1" in
		-h | --help )
			echo "./clean_mission_directory.sh <OPTIONS>"
			echo "-v or --verbose removes files using verbose flag"
			echo "-h or --help prints this message"
			exit 2
			;;
		-v | --verbose )
			VERBOSE="-v"
			shift 1
			;;
		-- )
			shift;
			break
			;;
		* )
			echo "Unexpected option: $1"
			;;
	esac
done

#-------------------------------------------------
# Part 2: Remove all the files
#-------------------------------------------------

rm -rf ${VERBOSE}  MOOSLog_*
rm -f  ${VERBOSE}  *~
rm -f  ${VERBOSE}  *.moos++
rm -f  ${VERBOSE}  .LastOpenedMOOSLogDirectory
