from SWAPRsqlite import *
from SWAPRstrings import *
# from SWAPRquestions import *
import csv

# Column numbers for WebAssign files
wIDcol = 1  # student's unique WebAssign ID ($STUDENT in WebAssign Perl) (default 1)
studentLinkCol = 4      # submitted YouTube URL (default 4)
expertLinkCol = 2       # expert-graded YouTube URLs
studentResponseeCol = 4    # start of student responses
# gradeCol = 3            # Column which starts the expert grades
studentResponseCol = 4    # Column which starts the student grades


def parseLinksFile(filename,db,labNumber,skipLinkless = False, linkCol = 4, verbose = False):
    # TODO: in the database, the URL of a student who did not submit a URL should be NULL, not ''

    # Reads a Webassign-formatted tab-delimited .csv file containing YouTube links submitted by students.
    #
    # When you download the .csv file, you must inclide the student responses, not just their scores. Scores are optional; the parser knows to ignore them.

    data = []
    with open(filename, 'rU') as csvfile:
        inputFile = csv.reader(csvfile, delimiter=',', quotechar='"')
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
                URL=getYoutubeLink(data[line][linkCol])
                if URL not in ['',None] or not skipLinkless:
                    # if skipLinkless, then we won't add people who haven't submitted links
                    if verbose:
                        print('Adding submission: wID='+wID+', URL='+URL+', labNumber='+str(labNumber))
                    if URL == '':
                        URL = None
                    db.addSubmission(wID,URL,labNumber)
        line += 1
    db.conn.commit()

def parseExpertsFile(filename,db,labNumber,gradeCol = 3):
    # We write the experts file ourselves, so we use a less irritating format than the WebAssign .csv's we have to use for the student data

    # SAMPLE EXPERT FILE CONTENTS : MAKE SURE TO USE TABS ========
    # Fullname  Username    StudentID   Link    Grade       Hidden          
    # expert1   -   e1-z56-0mjg 0   0   0   0   0   1   0
    # expert1   -   c5lqLddAGTU 3   2   1   2   4   4   0
    # expert1   -   Tqo8fb3t1vY 0   0   0   2   2   1   0
    # expert1   -   Vw-9d0ey67k 0   0   0   0   0   1   0
    # expert1   -   1SYju-Vb1i0 0   1   0   1   1   1   1
    # END SAMPLE =================================================
    linkCol = 2
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
                    URL = getYoutubeLink(data[line][linkCol])
                    grade = data[line][gradeCol:-2]
                    for i in range(len(grade)):
                        itemIndex = i+1
                        response = grade[i]
                        hidden = data[line][-2]
                        practice = data[line][-1]
                        db.cursor.execute("INSERT INTO experts VALUES (NULL, ?, ?, ?, ?, ?, ?)", [labNumber, URL, itemIndex, response, hidden, practice])
        line += 1
    db.conn.commit()
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

        questionCols = []   # a list of [wQuestion,column] which shows which column corresponds to the start of the responses to which wQuestion

        while not foundStart:    #Seek out the first line of student data
            if len(data[line]) >= 1:
                if data[line][0] == "Questions":
                    for entry in data[line]:
                        if re.match('[0-9]',entry):    # Check to see if we've got a question number
                            questionCols.append([int(entry),data[line].index(entry)])
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
                    fullName = data[line][0]

                    # db.cursor.execute("INSERT INTO students (fullName, wID) VALUES (?,?)",[fullName,wID])


                    for i in range(len(questionCols)):  # go over every question
                        qStart = questionCols[i][1]  # this question starts at this column
                        j = 0
                        wQuestion = questionCols[i][0]
                        db.cursor.execute("SELECT assignments.URL FROM assignments, questions WHERE assignments.questionIndex = questions.questionIndex AND questions.wQuestion = ? AND assignments.labNumber = questions.labNumber AND assignments.labNumber = ? AND assignments.wID = ?",[wQuestion,labNumber, wID])
                            

                        URL = db.cursor.fetchone()
                        try:
                            URL = str(URL[0])
                        except:
                            db.cursor.execute("SELECT assignments.URL FROM assignments, questions WHERE assignments.questionIndex = questions.questionIndex AND questions.wQuestion = ? AND assignments.labNumber = questions.labNumber AND assignments.labNumber = ? AND assignments.wID = ?",[wQuestion,labNumber, 'default'])
                            URL = db.cursor.fetchone()
                            try:
                                URL = str(URL[0])
                            except:
                                print('Response has invalid URL: URL='+str(URL)+', wID='+wID)
                            # 5/0
                        # if wID == 'adeaton6@gatech':
                        #     print(URL)
                        while j + qStart < len(data[line]):
                            # try:
                            itemIndex = j+1
                            response = data[line][j+qStart]
                            # if labNumber == 2:
                            #     print(filename+'\t'+wID+'\t'+response)
                            if response == '':
                                response = None
                            # We're going to go ahead and stick in the URL to which this response belongs
                            try:
                                db.cursor.execute("INSERT INTO responses VALUES(NULL, ?, ?, ?, ?, ?, ?)", [labNumber, wID, wQuestion, URL, itemIndex, response])
                            except:
                                print("Non-Unicode string in "+filename+" line "+str(line))
                                # db.addResponse( labNumber, wID, questionCols[i][0], j+1, data[line][j+qStart])
                            # except:
                            #     print(wID + ' response for lab '+str(labNumber)+' could not be added to database: '+data[line][j+qStart])
                            j += 1
                            if j + qStart in [entry[1] for entry in questionCols]:
                                break

            line += 1
        db.conn.commit()