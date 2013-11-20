from __future__ import division, print_function
from SWAPRsqlite import *
from SWAPRrubric import *

def createFinalGradesTable(db):
    db.cursor.execute("CREATE TABLE IF NOT EXISTS grades (labNumber int, wID text, URL text, finalGrade number DEFAULT 0, finalGradeVector text)")
    db.conn.commit()

def setGrade(db,URL,labNumber, calibrated = True):
    # We want to calculate the final grade for a given URL
    # We must know which rubric items count toward the grade
    # We must know what each response is worth for each item

    # Get the wID which submitted this video
    db.cursor.execute("SELECT wID FROM submissions WHERE labNumber = ? AND URL = ?",[labNumber,URL])
    data = db.cursor.fetchall()
    if len(data) != 1:
        print("URL "+URL+" belongs to zero or more than one people!")
    else:
        submitterwID = str(data[0][0])


    # TODO: make this work for any number of weight elements, not just 6
    # Gather the weights of everyone who graded the URL
    db.cursor.execute("SELECT DISTINCT responses.wID, weight1, weight2, weight3, weight4, weight5, weight6 FROM responses, weightsBIBI, submissions WHERE submissions.URL = responses.URL AND responses.URL = ? AND responses.wID = weightsBIBI.wID AND responses.labNumber = ? AND weightsBIBI.labNumber = responses.labNumber AND submissions.labNumber = responses.labNumber ORDER BY responses.wID",[URL,labNumber])
    weights = [ [str(entry[0]), [float(entry[i+1]) for i in range(6)] ]for entry in db.cursor.fetchall()]
    # Make a dictionary of weights keyed to unique wIDs 
    weightsDict = {}
    for entry in weights:
        weightsDict.update({entry[0]: entry[1]})
    weights = weightsDict
    # print(weights)

    db.cursor.execute("SELECT score FROM responses, responseKeys WHERE URL = ? and responses.labNumber = responseKeys.labNumber AND responses.labNumber = ? and wID = ? ORDER BY responses.itemIndex",[URL,labNumber,submitterwID])
    # Get the indices of the graded items for this rubric (TODO: we should only need to do this once per grade assignment)
    db.cursor.execute("SELECT itemIndex FROM rubrics WHERE labNumber = ? AND graded ORDER BY itemIndex",[labNumber])
    itemIndices = [int(entry[0]) for entry in db.cursor.fetchall()]

    # Gather those people's raw responses and the corresponding scores
    URLresponses = {}
    for wID in weights.keys():
        db.cursor.execute("SELECT responses.response, score FROM responses, rubrics, responseKeys K WHERE URL = ? AND wID = ? AND rubrics.labNumber = responses.labNumber AND K.labNumber = responses.labNumber AND responses.labNumber = ? AND rubrics.itemIndex = responses.itemIndex AND rubrics.itemIndex = K.itemIndex AND responses.response = K.response AND rubrics.graded ORDER BY responses.itemIndex",[URL,wID,labNumber])
        data = [entry for entry in db.cursor.fetchall()]
        thisResponse = [entry[0] for entry  in data]
        for i in range(len(thisResponse)):
            try:
                thisResponse[i] = float(thisResponse[i])
            except:
                thisResponse[i] = None

        thisScore = [float(entry[1]) for entry in data]
        for i in range(len(thisScore)):
            try:
                thisScore[i] = float(thisScore[i])
            except:
                thisScore[i] = None

        URLresponses.update({wID:[weights[wID],thisResponse,thisScore]})


    db.cursor.execute("SELECT COUNT(itemIndex) FROM rubrics WHERE rubrics.graded AND labNumber = ?",[labNumber])    # we shouldn't need to do this for every wID
    R = int(str(db.cursor.fetchone()[0]))
    # print(R)
    numerators = R*[0]
    rawNumerators = R*[0]
    denominators = R*[0]
    rawDenominators = R*[0]
    # print('Grading '+URL+'...')
    # print('Grader: '+submitterwID)
    # print(str(len(URLresponses))+' responders')
    for entry in URLresponses.values():
        weight = entry[0]
        # print('Weight='+str(weight))
        score = entry[2]
        # print('Score='+str(score))
        # Now, we construct an item-by-item weighted average
        if sum(weight) > 0 and len(score) == R:
            for i in range(R):
                # if calibrated:
                # Calibrated
                numerators[i] += weight[i]*score[i]    # Calibrated
                denominators[i] += weight[i]
                # else:
                # Raw
                rawNumerators[i] += score[i]   # Uncalibrated
                rawDenominators[i] += 1

    # If all the graders have weight 0 for a particular item, we give the student the student's own grade instead. Don't make the SQLite query unless we have to.
    selfGrade = None
    # print('Submitter wID:'+submitterwID+' denominators: '+str(denominators))
    for i in range(R):
        if denominators[i] == 0:
            # print('blarg!')
            if selfGrade == None:
                db.cursor.execute("SELECT score, responses.itemIndex FROM responses, responseKeys, rubrics WHERE rubrics.labNumber = responses.labNumber AND responseKeys.labNumber = responses.labNumber AND responses.labNumber = ? AND wID = ? AND URL = ? AND responses.itemIndex = responseKeys.itemIndex AND rubrics.itemIndex = responses.itemIndex AND rubrics.graded ORDER BY responses.itemIndex",[labNumber,submitterwID,URL])
                data = [entry for entry in db.cursor.fetchall()]
                selfGradesDict = {}
                for entry in data:
                    # itemIndex: selfScore
                    selfGradesDict.update({ int(entry[1]): float(entry[0]) })
                # We have to make the selfGrade
                selfGrade = []
                # ...but we might not have to do the maxGrade
                maxGrade = None
                # someone might score some but not all of their own items, so we need to make sure that we handle each graded itemIndex explicitly rather than just the ordered selfGrade list
                for j in range(R):
                    try:
                        selfGrades.append(selfGradesDict[itemIndices[j]])
                    except:
                        selfGrade.append(None)
                        # If the student didn't assign a grade to their own video, then we give them the max score for that item. Again, don't make the SQLite query unless we need to
                        if maxGrade == None:
                            # THIS ASSUMES RESPONSE=0 CORRESPONDS TO THE MAXIMUM SCORE
                            db.cursor.execute("SELECT score FROM responseKeys K, rubrics R WHERE K.labNumber= R.labNumber AND R.labNumber = ? AND response = 0 AND R.itemIndex = K.itemIndex AND R.graded ORDER BY K.itemIndex",[labNumber])
                            maxGrade = [float(entry[0]) for entry in db.cursor.fetchall()]
            elif selfGrade[i] != None:
                numerators[i] = selfGrade[i]
                rawNumerators[i] = selfGrade[i]
            else:
                numerators[i] = maxGrade[i]
                rawNumerators[i] = maxGrade[i]
            denominators[i] = 1
            rawDenominators[i] = 1



    finalGradeVector = [numerators[i]/denominators[i] for i in range(R)]
    finalGrade = sum(finalGradeVector)

    finalRawGradeVector = [rawNumerators[i]/rawDenominators[i] for i in range(R)]
    finalRawGrade = sum(finalRawGradeVector)

    # print("finalGradeVector="+str(finalGradeVector))
    # print("finalRawGradeVector="+str(finalRawGradeVector))
    # print("itemIndices="+str(itemIndices))

    # Put the itemgrades in the itemgrades table, and the finalgrades in the finalgrades table
    for i in range(len(finalGradeVector)):
        db.cursor.execute("INSERT INTO itemGrades VALUES (NULL,?,?,?,?,?,1)",[labNumber,submitterwID,URL,itemIndices[i],finalGradeVector[i]])

    for i in range(len(finalRawGradeVector)):
        db.cursor.execute("INSERT INTO itemGrades VALUES (NULL,?,?,?,?,?,0)",[labNumber,submitterwID,URL,itemIndices[i],finalRawGradeVector[i]])

    db.cursor.execute("INSERT INTO finalGrades VALUES (NULL,?,?,?,?,1)",[labNumber, submitterwID, URL, finalGrade])
    db.cursor.execute("INSERT INTO finalGrades VALUES (NULL,?,?,?,?,0)",[labNumber, submitterwID, URL, finalRawGrade])

    # print(finalGrade)

    # Insert the grades into the database
    # db.cursor.execute("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?, ?)",[labNumber,wID,URL,finalGrade,listToString(finalGradeVector),rawGrade,listToString(rawGradeVector)])
            # db.conn.commit()


def assignGrades(db,labNumber, calibrated = True):
    db.cursor.execute("SELECT wID, URL FROM submissions WHERE labNumber = ?", [labNumber])
    data = db.cursor.fetchall()
    for d in data:
        if str(d[1]) not in ['', None, 'NULL','None']:
            # print('Sending to setGrade(): '+str(d[1]))
            # Assign grades to students who submitted videos
            setGrade(db,str(d[1]),labNumber,calibrated)

    db.conn.commit()

def printGradesReport(db, filename, labNumber):
    maxScore = getMaxScore(db,labNumber)
    # print(maxScore)
    # R=Number of items in rubric
    db.cursor.execute("SELECT COUNT(*) FROM rubrics WHERE graded AND labNumber = ?",[labNumber])
    R = int(db.cursor.fetchone()[0])
    db.cursor.execute("SELECT G.wID, grade, weightSum FROM finalGrades G, weightsBIBI W WHERE G.wID = W.wID AND G.labNumber = W.labNumber AND G.labNumber = ? AND grade IS NOT NULL AND calibrated",[labNumber])
    with open(filename,'w') as output:
        output.write('Student\tPresentation Grade\tCalibration Grade\n')
        for student in db.cursor.fetchall():
            # print(student)
            peerGrade = float(student[1])*(100/maxScore)
            calibrationGrade = 100*float(student[2])/(6)
            output.write(str(student[0])+'\t'+str(peerGrade)+'\t'+str(calibrationGrade)+'\n')
