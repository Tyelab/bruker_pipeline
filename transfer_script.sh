#!/bin/bash

for directory in *
    do
        if [[ -d $directory ]]; then
            echo "Copying: " $directory
            date=$(echo $directory | cut -d '_' -f 1 )
            subject=$(echo $directory | cut -d '_' -f 2 )
            rsync -rpP --remove-source-files $directory /snlkt/data/_DATA/specialk_cs/2p/raw/$subject/$date/
        fi
    done

find . -type d -empty -print -delete