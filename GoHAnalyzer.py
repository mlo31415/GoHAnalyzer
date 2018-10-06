# GoH Analyzer
#
# A program to analyze Fancy 3 to
#   a) enumerate all conventions and create lists of their GoHs
#   b) Enumerate all people and create lists of their recognition
#   and c) compare the two noting discrepancies
#
# This works entirely on a local copy of Fancy 3 as created by FancyDownloader

from xmlrpc import client
import xml.etree.ElementTree as ET
import os
import datetime
import base64
import time

# Find out where the local copy of Fancy 3 is

# Read through it looking at each page. If it's a people page, look for a recognition list.  If it's a convention page, try to decode its GoH list.