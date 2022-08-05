#--------------------------------------------------------
# The CMakeLists.txt for:                       pChallenge_treasure
# Author(s):                              
#--------------------------------------------------------

SET(SRC
  Challenge_treasure.cpp
  Challenge_treasure_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(pChallenge_treasure ${SRC})

TARGET_LINK_LIBRARIES(pChallenge_treasure
   ${MOOS_LIBRARIES}
   mbutil
   m
   pthread)

