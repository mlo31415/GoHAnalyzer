import os
import re as Regex
import xml.etree.ElementTree as ET
import WikidotHelpers


#----------------------------------------------------------
# Return the actual page taking redirects into account.
def RedirectedPage(redirects, pagename):
    pagename=WikidotHelpers.Cannonicize(pagename)
    while pagename in redirects.keys():
        pagename=WikidotHelpers.Cannonicize(redirects[pagename])
    return pagename


#----------------------------------------------------------
# Scan a line looking for a row of a table.   If found, return the contents of the 1st cell.
def FindFirstCellContents(line, delimiter):
    loc1=line.find(delimiter)
    if loc1 == -1:
        return None
    loc2=line.find(delimiter, loc1+1)
    if loc2 == -1:
        return None
    return line[loc1+3:loc2].strip()


#----------------------------------------------------------
# Extract a conventions page name from cell contents.
# We must strip off the [[[]]] as well as get the page name, not the display name
def ExtractPageName(cell):
    cell=cell.strip()
    # There are two valid patterns here:
    #   [[[page-name]]]
    #   [[[page-name|display-name]]]
    m=Regex.match('\[\[\[(.+)\|(.+)\]\]\]', cell)
    if m is not None and len(m.groups()) > 0:
        return m.groups(0)[0].strip()

    m=Regex.match('\[\[\[(.+)\]\]\]', cell)
    if m is not None and len(m.groups()) > 0:
        return m.groups(0)[0].strip()

    return None


#----------------------------------------------------------
# Take a line of GoHs and extract the hyperlinked names only.
def ExtractGohs(cell):
    # Basically, the cell contents looks something like this:
    # [[[name 1]]], [[[name 2]]], name 3, [[[name 4]]], stuff
    # Go through the line removing all text that is at the 0 level of bracketing
    out=""
    i=0
    level=0
    while i < len(cell):
        c=cell[i]
        if c == "[":
            level=level+1
        if level > 0:
            out=out+c
        if c == "]":
            level=level-1
        i=i+1

    # The above line should now be: [[[name 1]]][[[name 2]]][[[name 4]]]
    # Split it on the ]]][[[ and then remove the brackets
    out=out[3:-3]
    return out.split("]]][[[")





#----------------------------------------------------------
# Scan a Fancy 3 page looking for a convention-series table
# A convention-series table is the first table and the first column is "Convention"
# Return a list of convention page names
def FindConventionSeriesTable(conName, lines):
    conventionColumnHeaders=["convention", "#"]
    gohColumnHeaders=["goh", "gohs", "guests of honor", "guests of honour"]

    i=0
    while i < len(lines):
        # Find the header of the 1st column
        # Look for a leading "||~" which indicates the start of a table
        if lines[i].strip().find("||~") != 0:
            i=i+1
            continue

        # Does this table look like a convention-series table?
        conventionColumnNumber=WikidotHelpers.FindTextInRow(lines[i], conventionColumnHeaders)
        gohColumnNumber=WikidotHelpers.FindTextInRow(lines[i], gohColumnHeaders)
        if conventionColumnNumber is None or gohColumnNumber is None:
            print("###### Could not find convention series table in page "+conName)
            return None
        break

    # OK, it looks like we have found a convention table.
    # Create a list of the convention names, which are found in the first column
    # There should be one line per convention
    conventions=[]
    i=i+1   # Skip over the table header
    while i < len(lines):
        line=lines[i].strip()
        i=i+1
        if line[:2] != "||":    # Have we fallen off the bottom of the table?
            break
        cell=WikidotHelpers.GetCellContents(line, conventionColumnNumber)
        pageName=ExtractPageName(cell)
        if pageName is None:
            continue
        cell=WikidotHelpers.GetCellContents(line, gohColumnNumber)
        gohList=ExtractGohs(cell)
        conventions.append((pageName, gohList))
    return conventions


#----------------------------------------------------------
# Scan a Fancy 3 page looking for a recognition block.
# This page should be a people page
# A recognition list is one or more recognition lines.  It is of the form "* <date> -- <comma separated list of pages>"
def FindRecognition(pageText):
    recognition=[]
    recFound=False
    i=2 # Recognition can never start on the first two lines.
    while i < len(pageText):
        rec=DecodeRecognitionLine(pageText[i])
        if rec is None:  # If this is not a recognition line, then it's either before the beginning of the recognition block or after its end
            if recFound:
                return recognition  # The block has terminated
            else:
                i=i+1
                continue  # No block has been found yet, continue searching
        recFound=True
        recognition.extend(rec)
        i=i+1

    return recognition


#----------------------------------------------------------
# Decode a recognition line into a list of recognitions. The line is comma-delimited.
# There are a number of recognition formats:
#   [[[<convention>]]]
#   [[[Best Blah Blah Hugo]]], [[[yyyy Best Blah Blah Hugo]]], [[[Best Blah Blah Hugo Award]]] (and probably others...)
#   [[[<award>]]]
#   [[[<award>]]] for [[[Best Blah]]]
def DecodeRecognitionLine(line):
    # Is this a recognition line?
    m=Regex.match('^\* (\d{4}) -- (.*)', line)
    if m is None or len(m.groups()) == 0:
        return None

    # It appears that we have found a recognition line
    year=m.groups(0)[0]
    list=m.groups(0)[1]

    # Some recognition items are bolded. so remove all instances of "**"
    list=list.replace("**", "")

    # Now split the list of recognition items by commas and then analyse each of them in turn
    # The commas need to be *outside* any [[[ ]]] since some conventions and awards have commas in their names
    bracketCount=0
    newlist=""
    for c in list:
        if c == "[":
            bracketCount=bracketCount+1
        elif c == "]":
            bracketCount=bracketCount-1
        elif c == "," and bracketCount == 0:
            c="%%%"
        newlist=newlist+c
    listitems=newlist.split("%%%")

    recognition=[]
    for item in listitems:
        item=item.strip()
        m=Regex.match('^\[\[\[(.*?)\]\]\]', item)  # Look for [[[<something>[]]]. Note that we're ignoring everything after the first [[[ ]]]
        if m is not None and len(m.groups()) > 0:
            recognition.append((WikidotHelpers.RemoveAlias(m.groups(0)[0]), year))
            continue
        m=Regex.match('^Toastmaster at \[\[\[(.*)\]\]\]', item)
        if m is not None and len(m.groups()) > 0:
            recognition.append((WikidotHelpers.RemoveAlias(m.groups(0)[0]), year))
            continue
        m=Regex.match('^MC at \[\[\[(.*)\]\]\]', item)
        if m is not None and len(m.groups()) > 0:
            recognition.append((WikidotHelpers.RemoveAlias(m.groups(0)[0]), year))
            continue
        print(">>>>Not recognized: "+item)
    return recognition


#----------------------------------------------------------
# Read a Fancy3 page into a list of lines
def ReadPage(pageName):
    global path, pageText, lines
    path=os.path.join("../site", pageName)
    # First, read the .txt file and see if this is a redirect.
    f=open(path+".txt", errors="ignore")
    pageText=f.readlines()
    f.close()
    lines=[l.strip() for l in pageText]  # Drop trailing "\n"
    lines=[l for l in lines if len(l) > 0 and len(l.strip()) > 0]  # Drop empty lines
    return lines

# ----------------------------------------------------------
# Read a page's tags
def ReadTags(pageName):
    tags=[]
    tagsEl=ET.ElementTree().parse(path+".xml").find("tags")
    if tagsEl is None:
        return tags
    tagElList=tagsEl.findall("tag")
    if len(tagElList) == 0:
        return tags
    for el in tagElList:
        tags.append(el.text)
    return tags

