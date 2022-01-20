#!/bin/bash

d=$(date "+%Y%m%d")
filename="$1-$d"


echo $1 > /logs/"$filename".log
echo $2 >> /logs/"$filename".log
echo $3 >> /logs/"$filename".log
