from sqlite1 import *
from SWAPRstrings import *
from SWAPRquestions import *
import csv

# Column numbers for WebAssign files
wIDcol = 1  # student's unique WebAssign ID ($STUDENT in WebAssign Perl) (default 1)
studentLinkCol = 4      # submitted YouTube URL (default 4)
expertLinkCol = 2       # expert-graded YouTube URLs
studentResponseeCol = 4    # start of student responses
gradeCol = 3            # Column which starts the expert grades
studentResponseCol = 4    # Column which starts the student grades


def parseLinksFile(filename,db,labNumber,skipLinkless = False):
    # TODO: in the database, the URL of a student who did not submit a URL should be NULL, not ''

    # Reads a Webassign-formatted tab-delimited .csv file containing YouTube links submitted by students.
    #
    # When you download the .csv file, you must inclide the student responses, not just their scores. Scores are optional; the parser knows to ignore them.

    data = []
    reportEntries = []
    with open(filename, 'rU') as csvfile:
        inputFile = csv.reader(csvfile, delimiter='\t', quotechar='|')
        # TODO: change this to operate directly on the file itself, not just blindly copy the whole file into memory
        for row in inputFile:
            data.append(row)

    line = 0
    foundStart = False
    while not foundStart:    #Seek out the first line of student data
        if len(data[line]) >= 1:
            if data[line][0] == 'Fullname': # The data starts right after the header line beginning with 'Fullname'
                foundStart = True
        line = line+1


    # Go through the data line-by-line, and add students + URLs to the database    
    while line in range(len(data)):
        if len(data[line]) > 1: # Make sure we don't have a blank line
            if data[line][0] != '': # Make sure we don't have one of the score lines
                wID=data[line][wIDcol]
                URL=getYoutubeLink(data[line][studentLinkCol])
                if URL is not '' or not skipLinkless:
                    # if skipLinkless, then we won't add people who haven't submitted links
                    db.addEntry(wID,URL,labNumber)
                    reportEntries.append([wID,URL,None])
        line += 1
    return reportEntries

def parseExpertsFile(filename,db,labNumber):
    # We write the experts file ourselves, so we use a less irritating format than the WebAssign .csv's we have to use for the student data

    # SAMPLE EXPERT FILE CONTENTS : MAKE SURE TO USE TABS ========
    # Fullname  Username    StudentID   Link    Grade       Hidden          
    # expert1   -   e1-z56-0mjg 0   0   0   0   0   1   0
    # expert1   -   c5lqLddAGTU 3   2   1   2   4   4   0
    # expert1   -   Tqo8fb3t1vY 0   0   0   2   2   1   0
    # expert1   -   Vw-9d0ey67k 0   0   0   0   0   1   0
    # expert1   -   1SYju-Vb1i0 0   1   0   1   1   1   1
    # END SAMPLE =================================================

    data = []
    reportEntries = []
    with open(filename, 'rU') as csvfile:
        inputFile = csv.reader(csvfile, delimiter='\t', quotechar='|')
        for row in inputFile:
            data.append(row)

    line = 1    # Data starts on the second line

    while line in range(len(data)):
        if len(data[line]) > 1: # Make sure we don't have a blank line
            if data[line][0] is not '': # Make sure we don't have one of the score lines
                if data[line][0][0] is not '#': # Make sure we don't have a commented line
                    URL = getYoutubeLink(data[line][expertLinkCol])
                    grade = data[line][gradeCol:-1]
                    wID = "dummy"+str(line)
                    db.addExpertURL(labNumber, URL, grade, hidden = data[line][-1])
                    reportEntries.append([wID,URL,None])
        line += 1
    return reportEntries

def parseResponsesFile(filename,db,labNumber):
    # parse student responses from the associated Webassign .csv file. As of October 2013, there are 3 such files associated with each lab; a practice file and a calibration file which each contains only fixed expert-graded URLs, and an evaluation file containing shuffled student URLs, the student's own URL, and one expert URL.

    # Regardless of which file we feed it, this function matches the student's responses up with the appropriate URL by mapping the given Webassign Question ID to that response's question index, and then mapping the question index to that student's URLsToGrade
    data = []
    with open(filename, 'rU') as csvfile:
        inputFile = csv.reader(csvfile, delimiter='\t', quotechar='|')
        for row in inputFile:
            data.append(row)


        line = 0

        questions = []
        foundStart = False
        while not foundStart:    #Seek out the first line of student data
            if len(data[line]) >= 1:
                if data[line][0] == "Questions":
                    for entry in data[line]:
                        if re.match('[0-9]',entry):    # Check to see if we've got a question number
                            questions.append(int(entry))
                if data[line][0] == 'Fullname':
                    foundStart = True
            line = line+1

        # Down in the student grade data, now
        while line in range(len(data)):
            if len(data[line]) > 1: # Make sure we don't have a blank line
                if data[line][0] != '': # Make sure we don't have one of the score lines
                    # Now we have a student in the grade file; find the right student in self
                    wID = data[line][wIDcol]

                    # Get the grades as one big ol' list of R*N ints or strings
                    collatedResponses = data[line][studentResponseCol:]
                    
                    if len(collatedResponses)%len(questions) != 0:
                        print('Wrong number of questions or responses! '+str(len(collatedResponses))+' '+str(len(questions))+' '+student.fullName)
                        
                    R = int(len(collatedResponses)/len(questions))
                    # Cut the collatedResponses up into one chunk per question (with R entries)
                    
                    URLsGraded = db.getURLsToGrade(wID,labNumber)
                    questionIndexDict = getQuestionIndexDict(db,labNumber)
                    questionPracticeDict = getQuestionPracticeDict(db,labNumber)

                    for i in range(len(questions)):
                        if collatedResponses[i*R] != '':   # Check that the student actually graded that video
                            # try:
                                # The questions are 1-indexed in the database
                                # TODO: rename the methods associated with this data to "responses" rather than "grades"
                            db.addGrade( wID, labNumber, URL = URLsGraded[questionIndexDict[questions[i]]-1], grade =collatedResponses[i*R:(i+1)*R], practice = questionPracticeDict[questions[i]] )
                            # except:
                                # print(wID+' grade assignment failed.')

            line += 1