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

import os
from os import listdir
from os.path import isfile, join
import re as Regex
import WikidotHelpers
import Fancy3Pages


#=======================================================================================
#=======================================================================================
# Main function
#=======================================================================================
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
print("***Reading Redirects...")
for pageName in allPages:
    # First, open the xml file and determine what type of page this is, and make lists
    #       An award page (note it in the awards list)
    #       A convention page

    lines=Fancy3Pages.ReadPage(pageName)
    if len(lines) == 0:
        continue
    m=Regex.match('\[\[module Redirect destination="(.+)"\]\]', lines[0])
    if m is not None and len(m.groups()) > 0:
        redirects[pageName]=WikidotHelpers.Cannonicize(m.groups()[0])
        continue
print("   "+str(len(redirects.keys()))+" redirects found")

print("***Analyzing pages...")
# conSerieses will be a dictionary.  The key will be the name of the convention series and the value will be a list of individual convention page names
conSerieses={}

# people will be a dictionary. The key will be the pagename of the person and the value will be a list of recognitions
people={}

# awards will be a list of award pages
awards=[]

for pageName in allPages:
    # We have located all the redirects, so we don't need to look at them again.
    if pageName in redirects.keys():
        continue

    # Open the xml file and determine what type of page this is, and make lists
    #       An award page (note it in the awards list)
    #       A convention page

    lines=Fancy3Pages.ReadPage(pageName)
    if len(lines) == 0:
        continue

    # See if it is tagged.
    # If it isn't tagged, then we can skip it.
    tags=Fancy3Pages.ReadTags(pageName)
    if len(tags) == 0:
        continue

    # We need a list of conventions-series.  A convention-series is a group of conventions (e.g., Boskone, Confusion, Worldcon)
    # For each convention-series, we'll build up a list of conventions from the table on the convention-series page
    # TODO: We need to handle the one-shot conventions
    # TODO: We need to handle the cases where there is a convention-series, but the individual conventions are also tagged "convention"
    i=0
    if "convention" in tags:
        # Not all pages tagged "convention" are convention-series pages. Convention-series pages contain a convention-series table.
        # Check if this is a convention-series
        # If it's a real convention-series, we add the convention name and page name to the list of conventions
        conlist=Fancy3Pages.FindConventionSeriesTable(lines)
        if conlist is not None:
            conSerieses[pageName]=conlist
        print(pageName+":  Convention: "+str(conlist))
        continue

    # We also want to create a list of people with their GoHships
    if "pro" in tags or "fan" in tags:
        reclist=Fancy3Pages.FindRecognition(lines)
        if reclist is not None:
            people[pageName]=reclist
        print(pageName+":  Recognition: "+str(reclist))
        continue

    # Maybe it's an award?
    if "award" in tags:
        awards.append(pageName)
        print(pageName+":  Award")

# Now we need to take the list of conventions stored in conSerieses and build up a list of the GoHs.
for conSeries in conSerieses:
    for con in conSeries:
        i=0

# OK, we've gathered the data.
# Take the awards data and remove awards from the recognition list
for pname in people.keys():
    reclist=people[pname]
    newreclist=[]
    for rec in reclist:
        conname=rec[0].lower()
        if WikidotHelpers.Cannonicize(conname) in awards:       # Drop recognitions which are an award
            continue
        if conname.find("hugo") > -1 and conname.find("best") > -1:     # Drop recognitions which are Hugo-related
            continue
        newreclist.append(rec)
    people[pname]=newreclist

# What we want to look at now are mismatches between the list of convention GoHs and the list of recognitions
i=0

