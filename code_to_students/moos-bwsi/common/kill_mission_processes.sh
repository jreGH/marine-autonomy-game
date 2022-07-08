#!/bin/bash

grep Run *moos | awk '{print $3}' | xargs -ixxx pkill -9 xxx
