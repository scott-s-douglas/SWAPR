from __future__ import division, print_function
from sqlite1 import *
from SWAPRrubric import *

def createFinalGradesTable(db):
    db.cursor.execute("CREATE TABLE IF NOT EXISTS grades (labNumber int, wID text, URL text, finalGrade number DEFAULT 0, finalGradeVector text)")
    db.conn.commit()

def setGrade(db,URL,labNumber, calibrated = True):
    # We want to calculate the final grade for a given URL
    # We must know which rubric items count toward the grade
    gradedDict = getRubricGradedDict(db,labNumber)
    # We must know what each response is worth for each item
    rubricValuesDict = getRubricValuesDict(db,labNumber)

    # TODO: make this work for any number of weight elements, not just 6
    db.cursor.execute("SELECT submissions.wID, response, weight1, weight2, weight3, weight4, weight5, weight6 FROM responses, weightsBIBI, submissions WHERE submissions.URL = responses.URL AND responses.URL = ? AND responses.wID = weightsBIBI.wID AND responses.labNumber = ? AND weightsBIBI.labNumber = responses.labNumber AND submissions.labNumber = ?",[URL,labNumber, labNumber])
    responses = db.cursor.fetchall()

    if len(responses) > 0:
        # print("URL has "+str(len(data))+" student responses.")
        doOnce = True
        for d in responses:
            response = stringToList(d[1])
            # First, remove all the non-graded items from the response
            grade = []
            for i in range(len(response)):
                if gradedDict[i+1]: # Items in the db are 1-indexed
                    try:
                        grade.append(int(response[i]))
                    except:
                        print('Error parsing grade for '+URL+': '+d[1])
                        break
            if doOnce:
                wID = str(d[0])
                numerators = len(grade)*[0]
                rawNumerators = len(grade)*[0]
                denominators = len(grade)*[0]
                rawDenominators = len(grade)*[0]
                doOnce = False
            weight = [float(entry) for entry in d[2:]]
            # Now, we construct an item-by-item weighted average
            for i in range(len(grade)):
                # if calibrated:
                # Calibrated
                numerators[i] += weight[i]*rubricValuesDict[i][grade[i]]    # Calibrated
                denominators[i] += weight[i]
                # else:
                # Raw
                rawNumerators[i] += rubricValuesDict[i][grade[i]]   # Uncalibrated
                rawDenominators[i] += 1

        # Now we need to actually assign the proper points, bearing in mind that some sets of graders might all have 0 weight for a given item. If such a case occurs, that item receives the grade from the student's own self-evaluation.
        
        db.cursor.execute("SELECT response FROM responses, submissions WHERE  responses.wID = submissions.wID AND responses.URL = submissions.URL AND submissions.URL = ? AND submissions.labNumber =?",[URL, labNumber])
        selfResponse = [str(item[0]) for item in db.cursor.fetchall()]
        if len(selfResponse) == 1:
            selfResponse = stringToList(selfResponse[0])
            selfGrade = []
            for i in range(len(selfResponse)):
                if gradedDict[i+1]: # Items in the db are 1-indexed
                    try:
                        selfGrade.append(int(selfResponse[i]))
                    except:
                        selfGrade.append(max(rubricValuesDict[len(selfGrade)+1].values()))

        finalGradeVector = []
        rawGradeVector = []

        for i in range(len(grade)):
            rawGradeVector.append(rawNumerators[i]/rawDenominators[i])
            rawGrade = sum(rawGradeVector)
            if denominators[i] > 0:
                finalGradeVector.append(numerators[i]/denominators[i])
            # If the graders all have 0 weight for this item, then get the student's own grade for that item
            elif len(selfGrade) == len(gradedDict): # Check to make sure the student actually graded their own video
                print("The owner of "+URL+" is receiving their own grade for item "+str(i)+".")
                finalGradeVector.append(selfGrade[i])

            else:
                # Otherwise, just give them full credit. INCENTIVE ALERT
                finalGradeVector.append(max(rubricValuesDict[i]))
                print("The owner of "+URL+" is receiving the max grade for item "+str(i)+".")
            # finalGradeVector = [numerators[i]/denominators[i] for i in range(len(grade))]
            finalGrade = sum(finalGradeVector)

        # Insert the grades into the database
        db.cursor.execute("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?, ?)",[labNumber,wID,URL,finalGrade,listToString(finalGradeVector),rawGrade,listToString(rawGradeVector)])
        # db.conn.commit()


def assignGrades(db,labNumber, calibrated = True):
    db.cursor.execute("SELECT wID, URL FROM submissions WHERE labNumber = ?", [labNumber])
    data = db.cursor.fetchall()
    for d in data:
        if str(d[1]) not in ['', None]:
            # Assign grades to students who submitted videos
            setGrade(db,str(d[1]),labNumber,calibrated)
        else:
            # Assign zeroes to students who did not submit videos
            db.cursor.execute("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?, ?)",[labNumber, str(d[0]), None, 0, listToString([0,0,0,0,0,0,]), 0, listToString([0,0,0,0,0,0,]) ])
    db.conn.commit()

def printGradesReport(db, filename, labNumber):
    maxScore = getMaxScore(db, labNumber)
    # print(maxScore)
    rubricValuesDict = getRubricValuesDict(db, labNumber)
    db.cursor.execute("SELECT submissions.wID, finalGrade, weightSum, finalGradeVector FROM submissions, grades, weightsBIBI WHERE submissions.wID = grades.wID AND submissions.wID = weightsBIBI.wID AND submissions.labNumber = weightsBIBI.labNumber AND submissions.labNumber = grades.labNumber AND submissions.labNumber = ?",[labNumber])
    with open(filename,'w') as output:
        output.write('Student\tPresentation Grade\tCalibration Grade\n')
        for student in db.cursor.fetchall():
            # print(student)
            peerGrade = float(student[1])*(100/maxScore)
            calibrationGrade = 100*float(student[2])/(len(rubricValuesDict))
            output.write(str(student[0])+'\t'+str(peerGrade)+'\t'+str(calibrationGrade)+'\n')
