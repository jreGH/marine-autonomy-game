#--------------------------------------------------------
# The CMakeLists.txt for:                       pChallenge_shoreside
# Author(s):                              
#--------------------------------------------------------

SET(SRC
  Challenge_shoreside.cpp
  Challenge_shoreside_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(pChallenge_shoreside ${SRC})

TARGET_LINK_LIBRARIES(pChallenge_shoreside
   ${MOOS_LIBRARIES}
   mbutil
   m
   pthread)

