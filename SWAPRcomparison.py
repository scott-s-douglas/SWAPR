# encoding: utf-8
from __future__ import division
from SWAPRsqlite import *
from SWAPRgrades import *
from SWAPRweights import *
from SWAPRstrings import getYoutubeID
import csv
import matplotlib.pyplot as plt
from numpy import median, mean, std
from scipy.stats import sem
from itertools import combinations
from random import shuffle
from SWAPRrubric import getMaxScore
import operator as op

class calibAlg:
    def __init__(self,name,sumFunc,weightFunc=weightBIBI,longName = '',offsetStyle = None):
        self.sumFunc = sumFunc
        self.weightFunc = weightFunc
        self.offsetStyle = offsetStyle
        self.name = name
        if longName == '':
            self.longName = name

def getNstudents(db,URL):
    db.cursor.execute("SELECT COUNT(DISTINCT wID) FROM responses WHERE URL = ? AND response is not NULL",[URL])
    return(int(db.cursor.fetchone()[0]))

def ncr(n, r):
    r = min(r, n-r)
    if r == 0: return 1
    numer = reduce(op.mul, xrange(n, n-r, -1))
    denom = reduce(op.mul, xrange(1, r+1))
    return numer//denom


def semFinite(data,N):
    'Standard error of the mean with finite population correction'
    # print(N)
    # print(len(data))
    if len(data) < 0.05*N:
        return sem(data)
    else:
        return sem(data)*((N-len(data))/(N-1))**0.5

def weightedSumMedianFallback(weights,scores):
    # Computes a weighted sum (weights[i][j]*scores[i][j])/sum(weights[i][j]) for each j; if all weights[i][j] are 0 for a given j, then finalGradeVector[j] is the median of all scores[i][j]
    R = len(weights[0]) # Number of graded rubric items
    N = len(weights)    # Number of peer grades
    numerators = [0]*R
    denominators = [0]*R
    for j in range(R):
        for i in range(N):
            if len(weights[i]) == R and len(scores[i]) == len(weights[i]):
                numerators[j] += weights[i][j]*scores[i][j]
                denominators[j] += weights[i][j]
        if denominators[j] == 0:
            numerators[j] = median([score[j] for score in scores])
            denominators[j] = 1
    finalGradeVector = [numerators[i]/denominators[i] for i in range(R)]
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def weightedSumMeanFallback(weights,scores):
    # Computes a weighted sum (weights[i][j]*scores[i][j])/sum(weights[i][j]) for each j; if all weights[i][j] are 0 for a given j, then finalGradeVector[j] is the mean of all scores[i][j]
    R = len(weights[0]) # Number of graded rubric items
    N = len(weights)    # Number of peer grades
    numerators = [0]*R
    denominators = [0]*R
    for j in range(R):
        for i in range(N):
            if len(weights[i]) == R and len(scores[i]) == len(weights[i]):
                numerators[j] += weights[i][j]*scores[i][j]
                denominators[j] += weights[i][j]
        if denominators[j] == 0:
            numerators[j] = mean([score[j] for score in scores])
            denominators[j] = 1
    finalGradeVector = [numerators[i]/denominators[i] for i in range(R)]
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def sumWinnersMedian(weights,scores):
    # For each j, picks out the highest weights[i][j] and assigns the corresponding score to finalGradeVector[j]. In the event of a tie, assign the median score. The median of an even number of scores is the mean of the two central scores.
    R = len(scores[0]) # Number of graded rubric items
    finalGradeVector = R*[0]
    for j in range(R):
        jWeights = [weight[j] for weight in weights if len(weight) == R]
        # Get the indices of the graders with the highest weights for item j
        winners = [index for index, weight in enumerate(jWeights) if weight == max(jWeights)]
        finalGradeVector[j] = median([scores[index][j] for index in winners if len(scores[index]) == R])
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def sumWinnersMean(weights,scores):
    # For each j, picks out the highest weights[i][j] and assigns the corresponding score to finalGradeVector[j]. In the event of a tie, assign the mean score.
    R = len(scores[0]) # Number of graded rubric items
    finalGradeVector = R*[0]
    for j in range(R):
        # Get the indices of the graders with the highest weights for item j
        jWeights = [weight[j] for weight in weights if len(weight) == R]
        winners = [index for index, weight in enumerate(jWeights) if weight == max(jWeights)]
        finalGradeVector[j] = mean([scores[index][j] for index in winners if len(scores[index]) == R])
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def sumNoZeroesMedian(weights,scores):
    # Throw out all zero-weighted scores and take the median of the remaining scores. Otherwise take the median of all scores.
    R = len(scores[0]) # Number of graded rubric items
    finalGradeVector = R*[0]
    for j in range(R):
        jWeights = [weight[j] for weight in weights if len(weight) == R]
        nonZeroes = [index for index, weight in enumerate(jWeights) if weight != 0]
        if len(nonZeroes) > 0:
            finalGradeVector[j] = median([scores[index][j] for index in nonZeroes if len(scores[index]) == R])
        else:
            finalGradeVector = [ median([score[j] for score in scores if len(score) == R]) for j in range(R) ]
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def sumMedian(weights,scores):
    # For each j, return the median of all scores[i][j]
    R = len(scores[0])
    finalGradeVector = [ median([score[j] for score in scores if len(score) == R]) for j in range(R) ]
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def sumMean(weights,scores):
    # For each j, return the mean of all scores[i][j]
    R = len(scores[0])
    finalGradeVector = [ mean([score[j] for score in scores if len (score) == R]) for j in range(R)  ]
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def weightedSumOffset(weights,scores,offsets,maxScores):
    # For each j, return the weighted mean of all scores[i][j] with a median fallback
    R = len(scores[0])
    N = len(scores)
    numerators = [0]*R
    denominators = [0]*R
    for j in range(R):
        numerators[j] = sum([abs(weights[i][j])*(scores[i][j]-offsets[i][j]) for i in range(N)])
        denominators[j] = sum([abs(weights[i][j]) for i in range(N)])
        if denominators[j] == 0:
            numerators[j] = median([scores[i][j] for i in range(N)])
            denominators[j] = 1
    finalGradeVector = [min([ max([numerators[j]/denominators[j], 0]), maxScores[j] ]) for j in range(R)]
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def weightedSumOffsetMeanFallback(weights,scores,offsets,maxScores):
    # For each j, return the weighted mean of all scores[i][j] with a median fallback
    R = len(scores[0])
    N = len(scores)
    numerators = [0]*R
    denominators = [0]*R
    for j in range(R):
        numerators[j] = sum([weights[i][j]*(scores[i][j]-offsets[i][j]) for i in range(N)])
        denominators[j] = sum([weights[i][j] for i in range(N)])
        if denominators[j] == 0:
            numerators[j] = mean([scores[i][j] for i in range(N)])
            denominators[j] = 1
    finalGradeVector = [min([ max([numerators[j]/denominators[j], 0]), maxScores[j] ]) for j in range(R)]
    finalGrade = sum(finalGradeVector)
    return finalGrade, finalGradeVector

def getWeightsScores(db,URL,weightFunc=weightBIBI,offsetStyle=None):
    # get the labNumber for that URL
    db.cursor.execute("SELECT labNumber FROM responses WHERE URL = ?",[URL])
    labNumber = int(db.cursor.fetchone()[0])

    # get the number of graded items (R) for that labNumber
    db.cursor.execute("SELECT count(itemIndex) FROM rubrics WHERE labNumber = ? AND graded",[labNumber])
    R = int(db.cursor.fetchone()[0])

    offsets = []
    if offsetStyle != None:
        db.cursor.execute("SELECT responses.URL, responses.wID, responses.itemIndex, weight, responseKeys.score FROM responses, weights, responseKeys, rubrics WHERE responses.URL = ? AND weights.labNumber = responses.labNumber AND responseKeys.labNumber = responses.labNumber AND rubrics.labNumber = responses.labNumber AND responses.wID = weights.wID AND weights.itemIndex = responses.itemIndex AND rubrics.itemIndex = responses.itemIndex AND responseKeys.itemIndex = responses.itemIndex AND responses.response = responseKeys.response AND weights.weightType = ? AND rubrics.graded ORDER BY responses.URL, responses.wID, responses.itemIndex",[URL,offsetStyle])
        data = db.cursor.fetchall()
        for wID, wIDoffsets in groupby(list(data), key=lambda x: str(x[1])):
            thisOffset = []
            for entry in list(wIDoffsets):
                # append every weight value
                thisOffset.append(float(entry[3]))
            if len(thisOffset) == R:
                offsets.append(thisOffset)    
    if weightFunc == None:
        db.cursor.execute("SELECT responses.URL, responses.wID, responses.itemIndex, 1, responseKeys.score FROM responses, responseKeys, rubrics WHERE responses.URL = ? AND responseKeys.labNumber = responses.labNumber AND rubrics.labNumber = responses.labNumber AND rubrics.itemIndex = responses.itemIndex AND responseKeys.itemIndex = responses.itemIndex AND responses.response = responseKeys.response AND rubrics.graded ORDER BY responses.URL, responses.wID, responses.itemIndex",[URL])
    else:
        db.cursor.execute("SELECT responses.URL, responses.wID, responses.itemIndex, weight, responseKeys.score FROM responses, weights, responseKeys, rubrics WHERE responses.URL = ? AND weights.labNumber = responses.labNumber AND responseKeys.labNumber = responses.labNumber AND rubrics.labNumber = responses.labNumber AND responses.wID = weights.wID AND weights.itemIndex = responses.itemIndex AND rubrics.itemIndex = responses.itemIndex AND responseKeys.itemIndex = responses.itemIndex AND responses.response = responseKeys.response AND weights.weightType = ? AND rubrics.graded ORDER BY responses.URL, responses.wID, responses.itemIndex",[URL,weightFunc.__name__])
    data = db.cursor.fetchall()
    # sort by wID
    weights = []
    scores = []
    for wID, wIDweights in groupby(list(data), key=lambda x: str(x[1])):
        thisWeight = []
        thisScore = []

        for entry in list(wIDweights):
            # append every weight value
            thisWeight.append(float(entry[3]))
            thisScore.append(float(entry[4]))
        if len(thisWeight) == len(thisScore) and len(thisWeight) == R:
            weights.append(thisWeight)
            scores.append(thisScore)

    return weights, scores, offsets, itemIndices

def randomCombinations(iterable, N, n):
    "Random selection of N combinations from itertools.combinations(iterable, n)"
    # Return all combinations if N >= (total number of combinations)
    # The number of combinations can get very large!
    # pool = tuple(combinations(iterable, n))
    # print(len(pool))
    # Ncombos = len(pool)
    # indices = sorted(random.sample(xrange(Ncombos), min(N,Ncombos)))
    # return list(pool[i] for i in indices)
    combos = []
    while len(combos) < min(N,ncr(len(iterable),n)):
        # print('Generating combo '+str(len(combos) + 1)+'...')
        indices = sorted(random.sample(xrange(len(iterable)), n))
        combo = [iterable[index] for index in indices]
        if combo not in combos: # This could take a very long time for large N, but hopefully not as long as generating tuple(combinations(iterable, n))
            combos.append(combo)
    return combos

def getExpertGrade(db,expertURL):
    db.cursor.execute("SELECT e.itemIndex, e.response, k.score FROM experts e, rubrics r, responseKeys k WHERE URL = ? AND e.labNumber = r.labNumber AND e.labNumber = k.labNumber AND e.itemIndex = r.itemIndex AND e.itemIndex = k.itemIndex AND e.response = k.response AND graded ORDER BY e.itemIndex",[expertURL])
    expertGradeVector = [float(entry[2]) for entry in db.cursor.fetchall()]
    expertGrade = sum(expertGradeVector)
    return expertGrade, expertGradeVector

def getCalibratedGrade(db,expertURL,alg):
    weights, scores, offsets = getWeightsScores(db,expertURL,alg.weightFunc,alg.offsetStyle)
    return alg.sumFunc(weights,scores)

def squareError(a,b):
    if len(a) == len(b):
        sqError = sum([ (a[i]-b[i])**2 for i in range(len(a))])
        return sqError
    else:
        print('Two lists are not the same length')

def generateSampleGrades(db,expertURL,n,alg,matchmaking='random'):
    db.cursor.execute("SELECT DISTINCT labNumber FROM experts WHERE URL = ?",[expertURL])
    labNumber = int(db.cursor.fetchone()[0])
    maxScore, maxScoreVector = getMaxScore(db,labNumber)
    if alg.offsetStyle == None:
        db.cursor.execute('''SELECT r.wID, r.itemIndex, k.score, w.weight
            FROM responses r, rubrics rub, responseKeys k, weights w
            WHERE 
                --only one URL
                r.URL = ? 
                --match wID
                AND r.wID = w.wID
                --match itemIndex
                AND r.itemIndex = rub.itemIndex 
                AND r.itemIndex = k.itemIndex 
                AND r.itemIndex = w.itemIndex 
                --match labNumber
                AND r.labNumber = rub.labNumber 
                AND r.labNumber = k.labNumber 
                AND r.labNumber = w.labNumber
                --only graded items
                AND rub.graded
                --match score to student response
                AND r.response = k.response 
                --get the right weight
                AND w.weightType = ?
                ORDER BY r.wID, r.itemIndex
                ''',[expertURL,alg.weightFunc.__name__])
        data = db.cursor.fetchall()
        studentScores = {}
        for wID, wIDgroup in groupby(data, key = lambda x: x[0]):
            wIDgroup = list(wIDgroup)
            thisItemIndices = [int(entry[1]) for entry in wIDgroup]
            thisScores = [float(entry[2]) for entry in wIDgroup]
            thisWeights = [float(entry[3]) for entry in wIDgroup]
            studentScores.update({wID:{'itemIndices':thisItemIndices,'scores':thisScores,'weights':thisWeights,'offsets':None}})
    else:
        db.cursor.execute('''SELECT r.wID, r.itemIndex, k.score, w.weight, off.weight
            FROM responses r, rubrics rub, responseKeys k, weights w, weights off 
            WHERE 
                --only one URL
                r.URL = ? 
                --match wIDs
                AND r.wID = w.wID
                AND r.wID = off.wID
                --match itemIndex
                AND r.itemIndex = rub.itemIndex 
                AND r.itemIndex = k.itemIndex 
                AND r.itemIndex = w.itemIndex 
                AND r.itemIndex = off.itemIndex 
                --match labNumber
                AND r.labNumber = rub.labNumber 
                AND r.labNumber = k.labNumber 
                AND r.labNumber = w.labNumber
                AND r.labNumber = off.labNumber
                --only graded items
                AND rub.graded
                --match score to student response
                AND r.response = k.response 
                --get the right weight
                AND w.weightType = ?
                --get the right offset
                AND off.weightType = ?
                ORDER BY r.wID, r.itemIndex
                ''',[expertURL,alg.weightFunc.__name__ if alg.weightFunc != None else 'weightBIBI',alg.offsetStyle])
        data = db.cursor.fetchall()
        studentScores = {}
        for wID, wIDgroup in groupby(data, key = lambda x: x[0]):
            wIDgroup = list(wIDgroup)
            thisItemIndices = [int(entry[1]) for entry in wIDgroup]
            thisScores = [float(entry[2]) for entry in wIDgroup]
            thisWeights = [float(entry[3]) for entry in wIDgroup]
            thisOffsets = [float(entry[4]) for entry in wIDgroup]
            studentScores.update({wID:{'itemIndices':thisItemIndices,'scores':thisScores,'weights':thisWeights,'offsets':thisOffsets}})

    # Now get the peerGroups we're going to use, and split their wIDs up into lists of the appropriate size
    db.cursor.execute('''SELECT g.peerGroup, g.wID from peerGroups p, groupMembers g
        WHERE
            --match peerGroup
            p.peerGroup = g.peerGroup
            --get the right nGroups
            AND p.nGroup = ?
            ORDER BY g.peerGroup
            ''',[n])
    data = db.cursor.fetchall()
    peerGroups = []
    for peerGroupID, group in groupby(data, key = lambda x: x[0]):
        peerGroups.append([peerGroupID,[str(entry[1]) for entry in group]])

    # MAIN SIMULATION LOOP
    db.cursor.execute("INSERT INTO simulations VALUES (NULL,?,?,?,?)",[expertURL,len(peerGroups),n,alg.name])
    expertFinalGrade, expertScore = getExpertGrade(db,expertURL)
    for peerGroup in peerGroups:
        peerGroupID = peerGroup[0]
        wIDs = peerGroup[1]
        # The pureOff style requires every score to be paired with a constant weight; by convention, weight = 1
        weights = [studentScores[wID]['weights'] for wID in wIDs] if alg.name != 'pureOff' else [ [1 for entry in studentScores[wID]['weights'] ] for wID in wIDs]
        scores = [studentScores[wID]['scores'] for wID in wIDs]
        # When drawing student responses from among the groupMembers table, we assert that every student has completed every graded item for every expert video. If this is not the case, then the first student in the peerGroup might not have the same itemIndices as everyone else, and the next line will cause bad behavior
        itemIndices = studentScores[wIDs[0]]['itemIndices']
        if alg.offsetStyle == None:
            calibratedFinalGrade, calibratedScore = alg.sumFunc(weights,scores)
        else:
            offsets = [studentScores[wID]['offsets'] for wID in wIDs]
            calibratedFinalGrade, calibratedScore = alg.sumFunc(weights,scores,offsets,maxScoreVector)
        # Add entries to simulatedScores
        for i in range(len(itemIndices)):
            db.cursor.execute("INSERT INTO simulatedScores VALUES ((SELECT max(simulation) from simulations), ?, ?, ?,?)",[peerGroupID,itemIndices[i],calibratedScore[i],expertScore[i]])
    db.conn.commit()

def generateSamplePeerGroups(db,Nmax,n,matchmaking='random'):
    # generates N list of groups of n students (peers) from among all the students who have graded ALL items of ALL expert-graded videos in ALL labs except labs 5 and 6
    db.cursor.execute('''SELECT r.wID, count(r.response)
            from responses r, experts e, rubrics b
            where
                r.URL = e.URL
                and r.itemIndex = e.itemIndex
                and r.labNumber = b.labNumber
                and r.itemIndex = b.itemIndex
                and b.graded and r.labNumber < 5
                and r.response is not null 
                GROUP BY r.wID order by r.wID''')
    data = [[str(entry[0]),int(entry[1])] for entry in db.cursor.fetchall()]
    validwIDs = [entry[0] for entry in data if entry[1]==120]
    # for wID, wIDgroup in groupby(data, key = lambda x: x[0]):
        # responses=[entry[1] for entry in wIDgroup]
    # if int(responses)==120:
    #     validwIDs.append(wID)
    # we now select N combinations at random from the list of all possible combinations of n validwIDs. If N is greater than the number of possible combinations, then we just use all possible combinations
    peerGroups = randomCombinations(validwIDs, Nmax, n)
    return peerGroups

def generateErrors(db,simulation):
    # generate all the square errors for each simulation (=a unique URL, N, n, and algorithm)
    db.cursor.execute('''INSERT INTO squareErrors (simulation, peerGroup, squareError) 
            SELECT simulation, peerGroup, SUM((simulatedScore - expertScore)*(simulatedScore-expertScore))
            FROM simulatedScores
            WHERE simulation = ?
            GROUP BY peerGroup''',[simulation])


