from __future__ import division, print_function
from SWAPRsqlite import *
from SWAPRrubric import *
from itertools import groupby
from numpy import median, mean
import scipy.stats

def createFinalGradesTable(db):
    db.cursor.execute("CREATE TABLE IF NOT EXISTS grades (labNumber int, wID text, URL text, finalGrade number DEFAULT 0, finalGradeVector text)")
    db.conn.commit()

def setGrade(db,labNumber,weightFunc,calibration = 'thisLab', test = False):
    # We want to calculate the final grade for a given URL
    # We must know which rubric items count toward the grade
    # We must know what each response is worth for each item


    db.cursor.execute("SELECT COUNT(itemIndex) FROM rubrics WHERE rubrics.graded AND labNumber = ?",[labNumber])    # we shouldn't need to do this for every wID
    R = int(str(db.cursor.fetchone()[0]))


    # Gather the weights and scores of everyone who graded every URL submitted this lab
    maxScore, maxScoreVector = getMaxScore(db,labNumber)

    if calibration == 'thisLab':
        db.cursor.execute("SELECT responses.URL, responses.wID, responses.itemIndex, weight, responseKeys.score FROM responses, weights, responseKeys, rubrics WHERE responses.URL is not null AND responses.URL in (select URL from submissions where URL is not null) AND responses.wID = weights.wID AND responses.labNumber = ? AND weights.labNumber = responses.labNumber AND responseKeys.labNumber = responses.labNumber AND rubrics.labNumber = responses.labNumber AND weights.itemIndex = responses.itemIndex AND rubrics.itemIndex = responses.itemIndex AND responseKeys.itemIndex = responses.itemIndex AND responses.response = responseKeys.response AND weights.weightType = ? AND rubrics.graded ORDER BY responses.URL, responses.wID, responses.itemIndex",[labNumber,weightFunc.__name__])
        data = db.cursor.fetchall()
        URLlist = []
        # sort by URL
        for URL, URLweights in groupby(data, key = lambda x: str(x[0])):
            responses = []
            # sort by responder wID
            for wID, wIDweights in groupby(list(URLweights), key=lambda x: str(x[1])):
                thisWeights = []
                thisScores = []
                for entry in list(wIDweights):
                    # append every weight value
                    thisWeights.append(float(entry[3]))
                    thisScores.append(float(entry[4]))
                responses.append([wID, thisWeights, thisScores])
            URLlist.append([URL,responses])

    elif calibration == 'prevLabs':
        # get the average weights
        # NOTE: In assigning lab5 grades in Fall 2013 (using prevLab calibration), we drew only DISTINCT full weight vectors from all previous labs. This would occasionally cause students' average weights for each itemIndex to be miscalculated, causing some (but not all) finalGrades to have an error of +/- 0.5 percentage points.
        # If this data needs to be replicated, the relevant query is
        #====================
        # db.cursor.execute("SELECT DISTINCT responses.wID, weight1, weight2, weight3, weight4, weight5, weight6 FROM responses, weightsBIBI, submissions WHERE submissions.URL = responses.URL AND responses.URL = ? AND responses.wID = weightsBIBI.wID AND submissions.labNumber = responses.labNumber ORDER BY responses.wID",[URL])
        #====================
        # Note that this statement queries only one URL at a time.
        db.cursor.execute("SELECT responses.wID, AVG(weight), weights.itemIndex FROM responses, weights WHERE responses.wID = weights.wID AND responses.itemIndex = weights.itemIndex and weights.weightType = ? GROUP BY responses.wID, weights.itemIndex  ORDER BY responses.wID, weights.itemIndex",[weightFunc.__name__])
        data = db.cursor.fetchall()
        # group by responder wID
        weightList = {}
        for wID, wIDweights in groupby(data, key = lambda x: str(x[0])):
            thisWeights = []
            wIDweights = list(wIDweights)
            for entry in wIDweights:
                thisWeights.append(float(entry[1]))
                # average weight vector for each lab
            weightList.update({ wID: thisWeights })

        # get the responses
        db.cursor.execute("SELECT responses.URL, responses.wID, responses.itemIndex, NULL, responseKeys.score FROM responses, responseKeys, rubrics WHERE responses.URL is not null AND responses.URL in (select URL from submissions where URL is not null) AND responses.labNumber = ? AND responseKeys.labNumber = responses.labNumber AND rubrics.labNumber = responses.labNumber  AND rubrics.itemIndex = responses.itemIndex AND responseKeys.itemIndex = responses.itemIndex AND responses.response = responseKeys.response AND rubrics.graded ORDER BY responses.URL, responses.wID, responses.itemIndex",[labNumber])
        data = db.cursor.fetchall()
        URLlist = []
        # sort by URL
        for URL, URLweights in groupby(data, key = lambda x: str(x[0])):
            responses = []
            # sort by responder wID
            for wID, wIDweights in groupby(list(URLweights), key=lambda x: str(x[1])):
                thisWeights = weightList[wID]
                thisScores = []
                for entry in list(wIDweights):
                    # append every weight value
                    thisScores.append(float(entry[4]))
                responses.append([wID, thisWeights, thisScores])
            URLlist.append([URL,responses])
            if test and URL == 'http://youtu.be/rsMPrU0BNgY':
                for entry in responses:
                    print('New response: '+str(entry))

    # elif calibration == 'median':
    #     db.cursor.execute("SELECT DISTINCT r.wID FROM responses r, submissions s WHERE r.URL=s.URL AND r.URL = ? AND r.labNumber=s.labNumber ORDER BY r.wID",[URL])
    #     weights = [ [str(entry[0]),[] ] for entry in db.cursor.fetchall()]
        # print(weights)

    for URLentry in URLlist:
        URL = URLentry[0]
        responses = URLentry[1]

        # Get the wID which submitted this video
        db.cursor.execute("SELECT wID FROM submissions WHERE labNumber = ? AND URL = ?",[labNumber,URL])
        data = db.cursor.fetchall()
        if len(data) != 1:
            print("URL "+URL+" belongs to zero or more than one people!")
        else:
            submitterwID = str(data[0][0])


        # Get the indices of the graded items for this rubric (TODO: we should only need to do this once per grade assignment)
        # TODO; do this when we're making the URLlist
        db.cursor.execute("SELECT itemIndex FROM rubrics WHERE labNumber = ? AND graded ORDER BY itemIndex",[labNumber])
        itemIndices = [int(entry[0]) for entry in db.cursor.fetchall()]

        # Gather those people's raw responses and the corresponding scores
        URLresponses = {}
        for entry in responses:
            wID = entry[0]
            thisWeights = entry[1]
            thisScores = entry[2]
            URLresponses.update({wID:[thisWeights,thisScores]})

        # print(R)
        numerators = R*[0]
        rawNumerators = R*[0]
        denominators = R*[0]
        rawDenominators = R*[0]
        # print('Grading '+URL+'...')
        # print('Grader: '+submitterwID)
        # print(str(len(URLresponses))+' responders')
        if calibration in ['thisLab','prevLabs']:
            for entry in URLresponses.values():
                weight = entry[0]
                score = entry[1]

                # Now, we construct an item-by-item weighted average
                if sum(weight) > 0 and len(score) == R:
                    for i in range(R):
                        numerators[i] += weight[i]*score[i]    # Calibrated
                        denominators[i] += weight[i]


                        rawNumerators[i] += score[i]   # Uncalibrated
                        rawDenominators[i] += 1
        elif calibration == 'median':
            # make the denominators all 1 (we won't use them), make each numerator the median score from all the graders
            for i in range(R):
                iScore = []
                for entry in URLresponses.values():
                    score = entry[2]    #TODO: is this right?
                    iScore.append(score[i])
                numerators[i] = median(iScore)
                denominators[i] = 1

        elif calibration == 'mean':
            # make the denominators all 1 (we won't use them), make each numerator the mean score from all the graders
            for i in range(R):
                iScore = []
                for entry in URLresponses.values():
                    score = entry[2]    #TODO: is this right?
                    iScore.append(score[i])
                numerators[i] = mean(iScore)
                denominators[i] = 1

        if test:
            print('New numerators: '+str(numerators))

        # If all the graders have weight 0 for a particular item, we give the student the student's own grade instead. Don't make the SQLite query unless we have to.
        selfGrade = None
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


        if calibration in ['thisLab','prevLabs']:
            finalGradeVector = [numerators[i]/denominators[i] for i in range(R)]
            finalGrade = sum(finalGradeVector)

            finalRawGradeVector = [rawNumerators[i]/rawDenominators[i] for i in range(R)]
            finalRawGrade = sum(finalRawGradeVector)
        elif calibration == 'median':
            finalRawGradeVector = numerators
            finalRawGrade = sum(finalRawGradeVector)

        if test:
                print(submitterwID+' new finalGrade: '+str(finalGrade))

        else:
        # Put the itemgrades in the itemgrades table, and the finalgrades in the finalgrades table
            if calibration in ['thisLab','prevLabs']:
                for i in range(len(finalGradeVector)):
                    db.cursor.execute("INSERT INTO itemGrades VALUES (NULL,?,?,?,?,?,?,1)",[labNumber,submitterwID,URL,itemIndices[i],finalGradeVector[i],finalGradeVector[i]*100/maxScoreVector[i]])
                db.cursor.execute("INSERT INTO finalGrades VALUES (NULL,?,?,?,?,?,1)",[labNumber, submitterwID, URL, finalGrade, finalGrade*100/maxScore])

            for i in range(len(finalRawGradeVector)):
                db.cursor.execute("INSERT INTO itemGrades VALUES (NULL,?,?,?,?,?,?,0)",[labNumber,submitterwID,URL,itemIndices[i],finalRawGradeVector[i],finalRawGradeVector[i]*100/maxScoreVector[i]])

            db.cursor.execute("INSERT INTO finalGrades VALUES (NULL,?,?,?,?,?,0)",[labNumber, submitterwID, URL, finalRawGrade, finalRawGrade*100/maxScore])
    if not test:
        db.conn.commit()


def assignGrades(db,labNumber,weightFunc,calibration = 'thisLab'):
    # if average cal, just use the average of the existing calibration scores instead of using the calibration score for this lab
    db.cursor.execute("SELECT wID, URL FROM submissions WHERE labNumber = ?", [labNumber])
    data = db.cursor.fetchall()
    for d in data:
        if str(d[1]) not in ['', None, 'NULL','None']:
            print('Sending to setGrade(): '+str(d[1]))
            # Assign grades to students who submitted videos
            setGrade(db,str(d[1]),labNumber,weightFunc,calibration)

    db.conn.commit()

def printGradesReport(db, filename, labNumber, reportWeights = True):
    maxScore = getMaxScore(db,labNumber)
    print("maxScore="+str(maxScore))
    # R=Number of items in rubric
    db.cursor.execute("SELECT COUNT(*) FROM rubrics WHERE graded AND labNumber = ?",[labNumber])
    R = int(db.cursor.fetchone()[0])
    if reportWeights:
        db.cursor.execute("SELECT G.wID, grade, weightSum FROM finalGrades G, weightsBIBI W WHERE G.wID = W.wID AND G.labNumber = W.labNumber AND G.labNumber = ? AND grade IS NOT NULL AND calibrated",[labNumber])
        with open(filename,'w') as output:
            output.write('Student\tPresentation Grade\tCalibration Grade\n')
            for student in db.cursor.fetchall():
                # print(student)
                peerGrade = float(student[1])*(100/maxScore)
                calibrationGrade = 100*float(student[2])/(R)
                output.write(str(student[0])+'\t'+str(peerGrade)+'\t'+str(calibrationGrade)+'\n')
    else:
        db.cursor.execute("SELECT G.wID, grade FROM finalGrades G WHERE G.labNumber = ? AND grade IS NOT NULL AND calibrated",[labNumber])
        with open(filename,'w') as output:
            output.write('Student\tPresentation Grade\n')
            for student in db.cursor.fetchall():
                # print(student)
                peerGrade = float(student[1])*(100/maxScore)
                output.write(str(student[0])+'\t'+str(peerGrade)+'\n')
                
                
##########################################################################################################################################
def getGaussianDistribution(numStudents, numBins):
    if numBins%2 == 0:
        sys.exit("Must have odd number of bins")
        
    #divide by 6 to get a skinnier bell curve, makes more people "average graders"
    cdf = scipy.stats.norm((numBins+2)/2, (numBins+2)/6).cdf([i for i in range(1, numBins+2)])
    
    percentDist = [cdf[i] - cdf[i-1] for i in range(1, len(cdf))]
    binPercents = [i/sum(percentDist) for i in percentDist]

    lowerBound = 0
    studentRanks = []
    
    for i in binPercents:
        studentRanks += [[lowerBound, lowerBound + int(i * numStudents)]]
        lowerBound += int(i* numStudents)
    #rounding the numbers (can't have a half a student) sometimes leads to us not including all students
    studentRanks[-1][-1] = numStudents
    
    #get the weights we need to give them
    weight = scipy.stats.norm((numBins)/2, (numBins)/4).cdf([i+.5 for i in range(numBins)])
    
    return [studentRanks, weight]
    
def assignGaussianWeights(db, labNumber, numBins):
    #get everyone who submitted a video, different query than before, asit uses ABS(CAST(experts.response AS FLOAT) - responses.response) to get the distance between the student's response and the expert's response
    db.cursor.execute("SELECT responses.wID, responses.URL, ABS(CAST(experts.response AS FLOAT) - responses.response), responses.itemIndex FROM responses, experts, rubrics WHERE responses.response >= 0 AND responses.itemIndex = experts.itemIndex AND responses.itemIndex = rubrics.itemIndex AND rubrics.graded AND rubrics.labNumber = responses.labNumber AND experts.labNumber = responses.labNumber AND responses.labNumber = ? and experts.URL = responses.URL AND experts.labNumber = responses.labNumber AND NOT experts.practice ORDER BY responses.WID, responses.itemIndex",[labNumber])
    #pairs = getExpertResponsePairs([entry for entry in db.cursor.fetchall()])
    
    wIDs = []
    sum = 0
    count = 0
    wID = "First"
    itemNumber = "First"
    data = []
    
    #gets the distance between the expert grade vector and student grade vector
    for entry in db.cursor.fetchall() + [["ASDLKJ", "asdf", 0, 0]]:
        if wID == "First" and itemNumber == "First":
            wID = str(entry[0])
            itemNumber = entry[3]
        if str(entry[0]) == wID and entry[3] == itemNumber:
            sum += entry[2]
            count += 1
        else:
            wIDs.append(wID)
            data.append([wID, sum/count, itemNumber])
            sum = entry[2]
            wID = str(entry[0])
            itemNumber = entry[3]
            count = 1
    #split up arrays by their item indices for simplicity sake...
    rankingArray = [[], [], [], [], [], []]
    for entry in data:
        rankingArray[int((entry[-1]-1)/2)].append(entry)
    
    numStudents = len(set(wIDs))


    studentRanks, weightDistribution = getGaussianDistribution(numStudents, numBins)
    #weights = {}
    #for name in set(wIDs):
    #    weights[name] = [0,0,0,0,0,0]

    #assign weights
    for arr in rankingArray:
        arr.sort(key = lambda x: x[1], reverse = True)
        for i in range(len(studentRanks)):
            bucket = arr[studentRanks[i][0]:studentRanks[i][1]]
            for entry in bucket:
                wID = entry[0]
                itemIndex = entry[2]
                weight = weightDistribution[i]
                #print wID, itemIndex, weight
                try:
                    db.cursor.execute("INSERT INTO weights VALUES (NULL,?,?,?,?,?)",[labNumber,wID,"gaussian", itemIndex,weight])
                    #db.cursor.execute("INSERT INTO WEIGHTS values (NULL,?,?,?,?,?,)", [labNumber, wID, "gaussian", itemIndex, weight])
                except:
                    print("Could not add "+wID+" lab "+str(labNumber)+" weight to database: too many responses. Might be enrolled in more than one section: TA or instructor?")
    db.conn.commit()


###only difference between this and setGrade is that the third input parameter is just a string, opposed to a function
def setGradeGaussian(db,labNumber, weightType, calibration = 'thisLab', test = False):
    # We want to calculate the final grade for a given URL
    # We must know which rubric items count toward the grade
    # We must know what each response is worth for each item


    db.cursor.execute("SELECT COUNT(itemIndex) FROM rubrics WHERE rubrics.graded AND labNumber = ?",[labNumber])    # we shouldn't need to do this for every wID
    R = int(str(db.cursor.fetchone()[0]))


    # Gather the weights and scores of everyone who graded every URL submitted this lab
    maxScore, maxScoreVector = getMaxScore(db,labNumber)

    if calibration == 'thisLab':
        db.cursor.execute("SELECT responses.URL, responses.wID, responses.itemIndex, weight, responseKeys.score FROM responses, weights, responseKeys, rubrics WHERE responses.URL is not null AND responses.URL in (select URL from submissions where URL is not null) AND responses.wID = weights.wID AND responses.labNumber = ? AND weights.labNumber = responses.labNumber AND responseKeys.labNumber = responses.labNumber AND rubrics.labNumber = responses.labNumber AND weights.itemIndex = responses.itemIndex AND rubrics.itemIndex = responses.itemIndex AND responseKeys.itemIndex = responses.itemIndex AND responses.response = responseKeys.response AND weights.weightType = ? AND rubrics.graded ORDER BY responses.URL, responses.wID, responses.itemIndex",[labNumber,weightType])
        data = db.cursor.fetchall()
        URLlist = []
        # sort by URL
        for URL, URLweights in groupby(data, key = lambda x: str(x[0])):
            responses = []
            # sort by responder wID
            for wID, wIDweights in groupby(list(URLweights), key=lambda x: str(x[1])):
                thisWeights = []
                thisScores = []
                for entry in list(wIDweights):
                    # append every weight value
                    thisWeights.append(float(entry[3]))
                    thisScores.append(float(entry[4]))
                responses.append([wID, thisWeights, thisScores])
            URLlist.append([URL,responses])

    elif calibration == 'prevLabs':
        # get the average weights
        # NOTE: In assigning lab5 grades in Fall 2013 (using prevLab calibration), we drew only DISTINCT full weight vectors from all previous labs. This would occasionally cause students' average weights for each itemIndex to be miscalculated, causing some (but not all) finalGrades to have an error of +/- 0.5 percentage points.
        # If this data needs to be replicated, the relevant query is
        #====================
        # db.cursor.execute("SELECT DISTINCT responses.wID, weight1, weight2, weight3, weight4, weight5, weight6 FROM responses, weightsBIBI, submissions WHERE submissions.URL = responses.URL AND responses.URL = ? AND responses.wID = weightsBIBI.wID AND submissions.labNumber = responses.labNumber ORDER BY responses.wID",[URL])
        #====================
        # Note that this statement queries only one URL at a time.
        db.cursor.execute("SELECT responses.wID, AVG(weight), weights.itemIndex FROM responses, weights WHERE responses.wID = weights.wID AND responses.itemIndex = weights.itemIndex and weights.weightType = ? GROUP BY responses.wID, weights.itemIndex  ORDER BY responses.wID, weights.itemIndex",[weightType])
        data = db.cursor.fetchall()
        # group by responder wID
        weightList = {}
        for wID, wIDweights in groupby(data, key = lambda x: str(x[0])):
            thisWeights = []
            wIDweights = list(wIDweights)
            for entry in wIDweights:
                thisWeights.append(float(entry[1]))
                # average weight vector for each lab
            weightList.update({ wID: thisWeights })

        # get the responses
        db.cursor.execute("SELECT responses.URL, responses.wID, responses.itemIndex, NULL, responseKeys.score FROM responses, responseKeys, rubrics WHERE responses.URL is not null AND responses.URL in (select URL from submissions where URL is not null) AND responses.labNumber = ? AND responseKeys.labNumber = responses.labNumber AND rubrics.labNumber = responses.labNumber  AND rubrics.itemIndex = responses.itemIndex AND responseKeys.itemIndex = responses.itemIndex AND responses.response = responseKeys.response AND rubrics.graded ORDER BY responses.URL, responses.wID, responses.itemIndex",[labNumber])
        data = db.cursor.fetchall()
        URLlist = []
        # sort by URL
        for URL, URLweights in groupby(data, key = lambda x: str(x[0])):
            responses = []
            # sort by responder wID
            for wID, wIDweights in groupby(list(URLweights), key=lambda x: str(x[1])):
                thisWeights = weightList[wID]
                thisScores = []
                for entry in list(wIDweights):
                    # append every weight value
                    thisScores.append(float(entry[4]))
                responses.append([wID, thisWeights, thisScores])
            URLlist.append([URL,responses])
            if test and URL == 'http://youtu.be/rsMPrU0BNgY':
                for entry in responses:
                    print('New response: '+str(entry))

    # elif calibration == 'median':
    #     db.cursor.execute("SELECT DISTINCT r.wID FROM responses r, submissions s WHERE r.URL=s.URL AND r.URL = ? AND r.labNumber=s.labNumber ORDER BY r.wID",[URL])
    #     weights = [ [str(entry[0]),[] ] for entry in db.cursor.fetchall()]
        # print(weights)

    for URLentry in URLlist:
        URL = URLentry[0]
        responses = URLentry[1]

        # Get the wID which submitted this video
        db.cursor.execute("SELECT wID FROM submissions WHERE labNumber = ? AND URL = ?",[labNumber,URL])
        data = db.cursor.fetchall()
        if len(data) != 1:
            print("URL "+URL+" belongs to zero or more than one people!")
        else:
            submitterwID = str(data[0][0])


        # Get the indices of the graded items for this rubric (TODO: we should only need to do this once per grade assignment)
        # TODO; do this when we're making the URLlist
        db.cursor.execute("SELECT itemIndex FROM rubrics WHERE labNumber = ? AND graded ORDER BY itemIndex",[labNumber])
        itemIndices = [int(entry[0]) for entry in db.cursor.fetchall()]

        # Gather those people's raw responses and the corresponding scores
        URLresponses = {}
        for entry in responses:
            wID = entry[0]
            thisWeights = entry[1]
            thisScores = entry[2]
            URLresponses.update({wID:[thisWeights,thisScores]})

        # print(R)
        numerators = R*[0]
        rawNumerators = R*[0]
        denominators = R*[0]
        rawDenominators = R*[0]
        # print('Grading '+URL+'...')
        # print('Grader: '+submitterwID)
        # print(str(len(URLresponses))+' responders')
        if calibration in ['thisLab','prevLabs']:
            for entry in URLresponses.values():
                weight = entry[0]
                score = entry[1]

                # Now, we construct an item-by-item weighted average
                if sum(weight) > 0 and len(score) == R:
                    for i in range(R):
                        numerators[i] += weight[i]*score[i]    # Calibrated
                        denominators[i] += weight[i]


                        rawNumerators[i] += score[i]   # Uncalibrated
                        rawDenominators[i] += 1
        elif calibration == 'median':
            # make the denominators all 1 (we won't use them), make each numerator the median score from all the graders
            for i in range(R):
                iScore = []
                for entry in URLresponses.values():
                    score = entry[2]    #TODO: is this right?
                    iScore.append(score[i])
                numerators[i] = median(iScore)
                denominators[i] = 1

        if test:
            print('New numerators: '+str(numerators))

        # If all the graders have weight 0 for a particular item, we give the student the student's own grade instead. Don't make the SQLite query unless we have to.
        selfGrade = None
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


        if calibration in ['thisLab','prevLabs']:
            finalGradeVector = [numerators[i]/denominators[i] for i in range(R)]
            finalGrade = sum(finalGradeVector)

            finalRawGradeVector = [rawNumerators[i]/rawDenominators[i] for i in range(R)]
            finalRawGrade = sum(finalRawGradeVector)
        elif calibration == 'median':
            finalRawGradeVector = numerators
            finalRawGrade = sum(finalRawGradeVector)

        if test:
                print(submitterwID+' new finalGrade: '+str(finalGrade))

        else:
        # Put the itemgrades in the itemgrades table, and the finalgrades in the finalgrades table
            if calibration in ['thisLab','prevLabs']:
                for i in range(len(finalGradeVector)):
                    db.cursor.execute("INSERT INTO itemGrades VALUES (NULL,?,?,?,?,?,?,1)",[labNumber,submitterwID,URL,itemIndices[i],finalGradeVector[i],finalGradeVector[i]*100/maxScoreVector[i]])
                db.cursor.execute("INSERT INTO finalGrades VALUES (NULL,?,?,?,?,?,1)",[labNumber, submitterwID, URL, finalGrade, finalGrade*100/maxScore])

            for i in range(len(finalRawGradeVector)):
                db.cursor.execute("INSERT INTO itemGrades VALUES (NULL,?,?,?,?,?,?,0)",[labNumber,submitterwID,URL,itemIndices[i],finalRawGradeVector[i],finalRawGradeVector[i]*100/maxScoreVector[i]])

            db.cursor.execute("INSERT INTO finalGrades VALUES (NULL,?,?,?,?,?,0)",[labNumber, submitterwID, URL, finalRawGrade, finalRawGrade*100/maxScore])
    if not test:
        db.conn.commit()
