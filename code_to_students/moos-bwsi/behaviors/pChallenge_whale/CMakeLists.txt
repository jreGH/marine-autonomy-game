#--------------------------------------------------------
# The CMakeLists.txt for:                       pChallenge_whale
# Author(s):                              
#--------------------------------------------------------

SET(SRC
  Challenge_whale.cpp
  Challenge_whale_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(pChallenge_whale ${SRC})

TARGET_LINK_LIBRARIES(pChallenge_whale
   ${MOOS_LIBRARIES}
   mbutil
   m
   pthread)

