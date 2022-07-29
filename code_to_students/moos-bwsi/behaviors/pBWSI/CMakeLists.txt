#--------------------------------------------------------
# The CMakeLists.txt for:                       pBWSI
# Author(s):                              
#--------------------------------------------------------

SET(SRC
  BWSI.cpp
  BWSI_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(pBWSI ${SRC})

TARGET_LINK_LIBRARIES(pBWSI
   ${MOOS_LIBRARIES}
   mbutil
   m
   pthread)

