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
        line=pageText[i]
        loc1=line.find("||~")
        if loc1 == -1:
            i=i+1
            continue
        loc2=line.find("||~", loc1+1)
        if loc2 == -1:
            i=i+1
            continue
        if loc1 == -1 or loc2 == -1:
            return None
        header=line[loc1+3:loc2].strip()

        # Does this table look like a convention-series table?
        if header.lower() in conventionColumnHeaders:
            break
        return None

        # Create a list of the convention names in this column
        # The remainder of the table is probably a list of conventions

