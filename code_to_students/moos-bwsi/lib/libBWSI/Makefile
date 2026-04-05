NAME=BWSI

INSTALL_LIB_DIR=${HOME}/moos-bwsi/lib
INSTALL_INC_DIR=${HOME}/moos-bwsi/lib/include

MOOS_INCLUDE=${HOME}/moos-ivp/include/ivp/
MOOSCORE_INCLUDE=${HOME}/moos-ivp/MOOS/MOOSCore/Core/libMOOS/include/

SRC=NodeReport.cpp ContactTracker.cpp
HEADERS=NodeReport.h ContactTracker.h

all: default install

default: ${SRC}
	g++ -Wall -std=c++11 -c ${SRC} -I${MOOS_INCLUDE} -I${MOOSCORE_INCLUDE}
	ar rcs lib${NAME}.a *.o

install:
	mkdir -p ${INSTALL_LIB_DIR}
	mkdir -p ${INSTALL_INC_DIR}
	cp lib${NAME}.a ${INSTALL_LIB_DIR}/
	cp ${HEADERS} ${INSTALL_INC_DIR}/

clean:
	rm -f *.o lib${NAME}.a
