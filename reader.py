#!/usr/bin/env python
import sys

# Read temp log file
logFile = sys.argv[1] if len(sys.argv) > 1 else '/tmp/artisan.log'
with open(logFile, 'r') as fp:
	print(fp.read())