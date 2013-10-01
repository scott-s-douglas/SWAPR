import re

def getYoutubeID(string):
    # Get the YouTube ID from a URL or other string
    if string is not '' and string is not None:
        ID = re.search('[a-zA-Z0-9_-]{11}', string)
        if ID is not None:
            if len(ID.group(0)) == 11:
                return ID.group(0)
    return ''

def getYoutubeLink(string, verbose = False):
    # Turn any string which contains a valid YouTube ID into a youtu.be link
    if string is not '' and string is not None:
        if len(getYoutubeID(string)) == 11:
            return 'http://youtu.be/'+getYoutubeID(string)
        elif verbose:
            print("Rejecting YouTube URL '"+string+"'")    
    return ''

def perlPerson(string):   # Generate a Perl-safe STUDENT ID (i.e. no @ sign)
    return re.sub('@','_',string);

def getPerlLinksLine(wID,URLsToGrade):
    outstring = '\t\"' + perlPerson(wID) + '\"=> [ ';
    for video in URLsToGrade:
        outstring += '\"' + getYoutubeID(video) +'\", ';
    outstring += '],\n';
    return outstring