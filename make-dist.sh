#!/bin/sh
DISTNAME="shil-1w1b-0.4"
rm -rf build $DISTNAME "$DISTNAME.zip"
/cygdrive/c/python24/python.exe setup.py py2exe --dist-dir="$DISTNAME"
zip -r "$DISTNAME.zip" $DISTNAME
