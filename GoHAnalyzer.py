# GoH Analyzer
#
# A program to analyze Fancy 3:
#   Look through all pages and
#       a) Create a list of all conventions
#       b) Create a list of all awards
#   Go over the pages again
#       If the first link on the page is the name of a convention and if this is not itsefl a convention page, then it's a convention instance:
#           Go through it and make a list of GoHs and save this information
#       If it's a people page, make a list of its recognitions that might be GoHships
#   Finally, compare the Goh and recognition lists, noting discrepancies
#
# This works entirely on a local copy of Fancy 3 as created by FancyDownloader

from xmlrpc import client
import xml.etree.ElementTree as ET
import os
from os import listdir
from os.path import isfile, join
import re as Regex
import datetime
import base64
import time
import WikidotHelpers

# Find out where the local copy of Fancy 3 is
# Change the working directory to the destination of the downloaded wiki
# The site is under Fancyclopedia/Python in a directiry named "site" which is parallel to the one containing this project.
cwd=os.getcwd()
path=os.path.join(cwd, "..\\site")
os.chdir(path)
os.chmod(path, 0o777)

# The local version of the site is a pair (sometimes also a folder) of files with the Wikidot name of the page.
# <name>.txt is the text of the current version of the page
# <name>.xml is xml containing meta date. The metadata we need is the tags
# If there are attachments, they're in a folden named <name>. We don't need to look at that in this program

# Create a list of the pages on the site by looking for .txt files and dropping the extension
allPages = [f[:-4] for f in listdir(".") if isfile(join(".", f)) and os.path.splitext(f)[1] == ".txt"]

# Redirects will be a dictionary.  The key will be a name of a redirect page and the value will be what it redirects to.
# Both the key and the value will be cannonicized
redirects={}

for pageName in allPages:
    # First, open the xml file and determine what type of page this is, and make lists
    #       An award page (note it in the awards list)
    #       A convention page

    path=os.path.join("../site", pageName)

    # First, read the .txt file and see if this is a redirect.
    f=open(path+".txt", "r")
    lines=[l[:-1] for l in f.readlines()]   # Drop trailing "\n"
    lines=[l for l in lines if len(l) > 0 and len(l.strip()) > 0]   # Drop empty lines
    if len(lines) == 0:
        continue
    m=Regex.match(Regex.escape('\[\[module Redirect destination="(.+)"\]\]'), lines[0])
    if m is not None and len(m.groups()) > 0:
        redirects[pageName]=WikidotHelpers.Cannonicize(m.groups()[0])
        continue

    # Not a redirect
    tagsEl=ET.ElementTree().parse(path+".xml").find("tags")
    if tagsEl is None:
        continue
    tagElList=tagsEl.findall("tag")
    if len(tagElList) == 0:  # No tags, must be a redirect or something else not interesting
        continue
    tags=[]
    for el in tagElList:
        tags.append(el.text)
    i=0

i=0