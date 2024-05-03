#!/bin/sh
pandoc -s --toc -c pandoc.css ${1} -o ${1%.*}.html

