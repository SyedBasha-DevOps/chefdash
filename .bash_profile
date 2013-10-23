#!/bin/sh

for dir in `ls -d */`; do
	TMPPATH=$TMPPATH:`pwd`/${dir%/}
done

P=$P:`pwd`/bin
files="`find bin -name *.py`"
if [ ! -z "$files" ]; then
	chmod +x $files
fi

export PATH=$PATH$P
export PYTHONPATH=$TMPPATH
