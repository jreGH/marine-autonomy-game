#--------------------------------------------------------
# The CMakeLists.txt for:                       pChallenge_shark_shark
# Author(s):                              
#--------------------------------------------------------

SET(SRC
  Challenge_shark_shark.cpp
  Challenge_shark_shark_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(pChallenge_shark_shark ${SRC})

TARGET_LINK_LIBRARIES(pChallenge_shark_shark
   ${MOOS_LIBRARIES}
   mbutil
   m
   pthread)

