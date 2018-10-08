import re as Regex


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
# Scan a Fancy 3 page looking for a convention-series table
# A convention-series table is the first table and the first column is "Convention"
# Return a list of convention page names
def FindConventionSeriesTable(pageText):
    conventionColumnHeaders=["convention"]

    # pageText is a list containing the lines in the page
    i=0
    while i < len(pageText):
        # Find the header of the 1st column
        # Look for a leading "||~" which indicates the start of a table
        header=FindFirstCellContents(pageText[i], "||~")
        if header is None:
            i=i+1
            continue

        # Does this table look like a convention-series table?
        if header.lower() not in conventionColumnHeaders:
            return None
        break

    # OK, it looks like we have found a convention table.
    # Create a list of the convention names, which are found in the first column
    # There should be one line per convention
    conventions=[]
    i=i+1   # Skip over the table header
    while i < len(pageText):
        line=pageText[i].strip()
        i=i+1
        if line[:2] != "||":    # Have we fallen off the bottom of the table?
            break
        cell=FindFirstCellContents(line, "||")
        pageName=ExtractPageName(cell)
        if pageName is not None:
            conventions.append(pageName)

    return conventions


#----------------------------------------------------------
# Scan a Fancy 3 page looking for a recognition list.
# This page should be a people page
# A recognition list is one or more items of the format * <date> -- <comma separated list of pages>
def FindRecognition(pageText):
    recognition=[]

    # First look for the "[[include recognition]]" line
    i=0
    while i < len(pageText):
        if pageText[i] == "[[include recognition]]\n":
            break
        i=i+1

    if i < len(pageText):
        while i < len(pageText):
            # We found it.  The following lines will be recognition lines
            m=Regex.match('\* (\d{4}) -- (.*)', pageText[i])
            if m is not None and len(m.groups()) > 0:
                year=m.groups(0)[0]
                list=m.groups(0)[1]

                # Now split the list of recognition items by commas and then analyse each of them in turm
                listitems=list.split(",")
                for item in listitems:
                    item=item.strip()
                    m=Regex.match('\[\[\[(.*)\]\]\]', item)     # Look for [[[<something>[]]]
                    if m is not None and len(m.groups()) > 0:
                        recognition.append((m.groups(0)[0], year))
                        continue
                    m=Regex.match('Toastmaster at \[\[\[(.*)\]\]\]', item)
                    if m is not None and len(m.groups()) > 0:
                        recognition.append((m.groups(0)[0], year))
                        continue
                    m=Regex.match('MC at \[\[\[(.*)\]\]\]', item)
                    if m is not None and len(m.groups()) > 0:
                        recognition.append((m.groups(0)[0], year))
                        continue
            i=i+1
    return recognition


