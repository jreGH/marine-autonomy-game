#--------------------------------------------------------
# The CMakeLists.txt for:                       pChallenge_fish
# Author(s):                              
#--------------------------------------------------------

SET(SRC
  Challenge_fish.cpp
  Challenge_fish_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(pChallenge_fish ${SRC})

TARGET_LINK_LIBRARIES(pChallenge_fish
   ${MOOS_LIBRARIES}
   mbutil
   m
   pthread)

