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
print("***Creating list of all pages")
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

print("***Checking redirects for loops")
for key in redirects.keys():
    val=key
    while val in redirects.keys():
        val=redirects[val]
        if val == key:
            print("######Loop in redirects: " + key)
            break

print("***Analyzing pages...")
# conSeriesDict will be a dictionary.  The key will be the name of the convention series and the value will be a list of individual convention page names
conSeriesDict={}    # This is tagged "con" and contains a convention series table
conSingletonList=[] # *List* of paged tagged "con" which doesn't
conSeriesSet=set()    # This will be a set containing all the individual conventions found in all the conSeries tables

# people will be a dictionary. The key will be the pagename of the person and the value will be a list of recognitions
people={}

# awards and will be a list of pages
fanfunds=[]
awards=[]

for pageName in allPages:
    # We have located all the redirects, so we don't need to look at them again.
    if pageName in redirects.keys():
        continue
    # Note that we now can be sure that pageName is a fully redirected pagename

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
        conlist=Fancy3Pages.FindConventionSeriesTable(pageName, lines, redirects)
        if conlist is not None and len(conlist) > 0:
            # A conlist is a list of tuples
            # Each tuple is a con name and a list of its GoHs
            conSeriesDict[pageName]=conlist   # This is a list of tuples of convention-name and goh-list
            print(pageName+":  Convention series: "+str(conlist))
            for cl in conlist:
                conSeriesSet.add(cl[0])
        else:
            conSingletonList.append(pageName)
            print(pageName+":  ConSingleton")
        continue

    # Removing entries in ConSingletonList which are pointed to by ConSeries series tables
    conSingletonList=[c for c in conSingletonList if c not in conSeriesSet]

    # We also want to create a list of people with their GoHships
    if "pro" in tags or "fan" in tags:
        reclist=Fancy3Pages.FindRecognition(lines)
        reclist=[(Fancy3Pages.RedirectedPage(redirects, r[0]), r[1]) for r in reclist] # Make sure that we only use fully redirected names
        if reclist is not None:
            people[pageName]=reclist
        print(pageName+":  Recognition: "+str(reclist))
        continue

    # Maybe it's an award?
    if "award" in tags:
        awards.append(WikidotHelpers.Cannonicize(Fancy3Pages.RedirectedPage(redirects, pageName)))
        print(pageName+":  Award")

    # Or a fan fund?
    if "fanfund" in tags:
        fanfunds.append(WikidotHelpers.Cannonicize(Fancy3Pages.RedirectedPage(redirects, pageName)))
        print(pageName+":  Fan Fund")

# OK, we've gathered the data.
# Take the awards and fanfund data and remove them from the recognition list
for pname in people.keys():
    reclist=people[pname]
    newreclist=[]
    for rec in reclist:
        conname=rec[0].lower()
        if WikidotHelpers.Cannonicize(conname) in awards:    # Drop recognitions which are an award
            continue
        if WikidotHelpers.Cannonicize(conname) in fanfunds:  # Drop recognitions which are a fanfund
            continue
        if conname.find("hugo") > -1 and conname.find("best") > -1:     # Drop recognitions which are Hugo-related
            continue
        if conname[5:] == "campbell-award":     # Ignore 'xxxx Campbell Award'
            continue
        newreclist.append(rec)
    people[pname]=newreclist

# What we want to look at now are mismatches between the list of convention GoHs and the list of recognitions
# First we walk the list of people and make list all recognitions which are not found on the convention side
countFailures=0
for pkey in people.keys():
    reclist=people[pkey]
    for rec in reclist:
        # A Rec is a tuple of a convention and a year
        gohList=Fancy3Pages.LookUpGohList(conSeriesDict, rec[0])
        if gohList is None:
            if rec[0] not in conSingletonList:      # We can't get the GoH list for singleton cons, so ignore them for now.
                print("***Couldn't find "+rec[0]+ " in conSeriesDict (person="+pkey+")")
                countFailures=countFailures+1
                i=0
print("\n"+str(countFailures)+" lookup failures found")


