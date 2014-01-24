# encoding: utf-8
from SWAPRsqlite import *
from SWAPRgrades import *
from SWAPRweights import *
from SWAPRstrings import getYoutubeID
import csv
import matplotlib.pyplot as plt
from numpy import median, mean, std
from itertools import combinations
from random import shuffle

class calibAlg:
    def __init__(self,name,sumFunc,weightFunc=weightBIBI,longName = ''):
        self.sumFunc = sumFunc
        self.weightFunc = weightFunc
        self.name = name
        if longName == '':
            self.longName = name

random.seed=(342394857928347)

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

def getWeightsScores(db,URL,weightFunc=weightBIBI):
    # get the labNumber for that URL
    db.cursor.execute("SELECT labNumber FROM responses WHERE URL = ?",[URL])
    labNumber = int(db.cursor.fetchone()[0])

    # get the number of graded items (R) for that labNumber
    db.cursor.execute("SELECT count(itemIndex) FROM rubrics WHERE labNumber = ? AND graded",[labNumber])
    R = int(db.cursor.fetchone()[0])

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

    return weights, scores

def random_combination(iterable, r):
    "Random selection from itertools.combinations(iterable, r)"
    pool = tuple(iterable)
    n = len(pool)
    indices = sorted(random.sample(xrange(n), r))
    return list(pool[i] for i in indices)

def getExpertGrade(db,expertURL):
    db.cursor.execute("SELECT e.itemIndex, e.response, k.score FROM experts e, rubrics r, responseKeys k WHERE URL = ? AND e.labNumber = r.labNumber AND e.labNumber = k.labNumber AND e.itemIndex = r.itemIndex AND e.itemIndex = k.itemIndex AND e.response = k.response AND graded ORDER BY e.itemIndex",[expertURL])
    expertGradeVector = [float(entry[2]) for entry in db.cursor.fetchall()]
    expertGrade = sum(expertGradeVector)
    return expertGrade, expertGradeVector

def getCalibratedGrade(db,expertURL,alg):
    weights, scores = getWeightsScores(db,expertURL,alg.weightFunc)
    return alg.sumFunc(weights,scores)

def squareError(a,b):
    if len(a) == len(b):
        sqError = sum([ (a[i]-b[i])**2 for i in range(len(a))])
        return sqError
    else:
        print('Two lists are not the same length')

def getSampleGrades(db,expertURL,n,N,alg,allCombinations=False):
    weights, scores = getWeightsScores(db,expertURL,alg.weightFunc)
    expertGrade,expertGradeVector = getExpertGrade(db,expertURL)
    grades = []
    gradeVectors = []
    squareDiffs = []
    Nstudents = len(weights)
    combos = [random_combination(range(Nstudents),n) for i in range(N)]
    counter = 1
    for combo in combos:
        if counter%(round(len(combos)/2)) == 0:
            print("Grading "+expertURL+": "+str(round(counter*100/round(len(combos))))+'%')
        counter += 1
        sampleWeights = [weights[j] for j in combo]
        sampleScores = [scores[j] for j in combo]
        grade, gradeVector = alg.sumFunc(sampleWeights,sampleScores)
        grades.append(grade)
        gradeVectors.append(gradeVector)
        sqDiff = squareError(gradeVector,expertGradeVector)
        squareDiffs.append(sqDiff)
    return expertGrade, grades, squareDiffs

# Define Algorithms
BIBI_1 = calibAlg("BIBI_1",weightedSumMedianFallback,weightBIBI,longName = u"Binary Item-by-Item ±1")
BIBI_0 = calibAlg("BIBI_0",weightedSumMedianFallback,weightDIBI_1,longName = u"Binary Item-by-Item ±0")
woMedian = calibAlg("woMedian",sumWinnersMedian,weightDIBI_1,longName = "Winners Only (Median)")
woMean = calibAlg("woMean",sumWinnersMean,weightDIBI_1,longName = "Winners Only (Mean)")
noZeroes = calibAlg("noZeroes",sumNoZeroesMedian,weightDIBI_1,longName = "No Zeroes")
medianAlg = calibAlg("median",sumMedian,longName = "Median")
meanAlg = calibAlg("mean",sumMean,longName = "Mean")
#gaussian = calibAlg("gaussian",sumMean,longName = "Gaussian")


calibAlgs = [BIBI_1,BIBI_0,woMedian,woMean,noZeroes,medianAlg,meanAlg]#, gaussian]
algNamesStrings=[alg.name for alg in calibAlgs]

plot = True
sample = True
gross = False
n=10
N=10000 # 149 students, so max number of groups is (N choose n)
if gross:
    with open('Comparisons.csv','w') as csvFile:
        csvWriter = csv.writer(csvFile, delimiter=',',quotechar='|',quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow([""]+algNamesStrings+["Experts"])

        for labNumber in [1,2,3,4]:
            print("Plotting Lab "+str(labNumber)+'...')
            db = SqliteDB("AnonymousCampus.sqlite")

            db.cursor.execute("SELECT DISTINCT URL FROM experts WHERE practice AND labNumber = ?",[labNumber])
            expertURLs = [str(entry[0]) for entry in db.cursor.fetchall()]


            doOnce = True   # do once PER LABNUMBER

            for i in range(len(expertURLs)):    # cycle over each video
                expertURL = expertURLs[i]
                BIBI_1Grade, BIBI_1Vector = getCalibratedGrade(db,expertURL,weightedSumMedianFallback,weightBIBI)
                BIBI_0Grade, BIBI_0Vector = getCalibratedGrade(db,expertURL,weightedSumMedianFallback,weightDIBI_1)
                winnersOnlyMedianGrade, winnersOnlyMedianVector = getCalibratedGrade(db,expertURL,sumWinnersMedian,weightDIBI_1)
                winnersOnlyMeanGrade, winnersOnlyMeanVector = getCalibratedGrade(db,expertURL,sumWinnersMean,weightDIBI_1)
                medianGrade, medianVector = getCalibratedGrade(db,expertURL,sumMedian)
                meanGrade, meanVector = getCalibratedGrade(db,expertURL,sumMean)
                expertGrade, expertVector = getExpertGrade(db,expertURL)
                R = len(expertVector)

                csvWriter.writerow([getYoutubeID(expertURL)+' score',BIBI_1Grade,BIBI_0Grade,winnersOnlyMedianGrade,winnersOnlyMeanGrade,medianGrade,meanGrade,expertGrade])

                calibratedVectors = [BIBI_1Vector,BIBI_0Vector,winnersOnlyMedianVector,winnersOnlyMeanVector,medianVector,meanVector]

                differenceVectors = [[calibratedVectors[l][m] - expertVector[m] for m in range(len(expertVector))] for l in range(len(calibratedVectors))]

                # Start gathering the means
                nAlgs = len(differenceVectors)   # "number of algorithms"
                nVids = len(expertURLs) # "number of URLs"
                if doOnce:
                    fig = plt.figure(figsize=(4*len(calibratedVectors),7.5))
                    fig.suptitle('Lab '+str(labNumber)+' Practice Videos (Campus)')
                    diffMeans = [0]*nAlgs
                    sqdiffMeans = [0]*nAlgs
                    doOnce = False
                # for ii in range(nAlgs):
                #     diffMeans[ii] += sum([abs(diff) for diff in differenceVectors[ii]])/len(expertURLs)

                # csvWriter.writerow([expertURL]+[str(sum([abs(entry) for entry in differenceVector])) for differenceVector in differenceVectors])
                for j in range(nAlgs):
                    # Calculate the difference measures
                    diff = 0
                    squareDiff = 0
                    for k in range(len(differenceVectors[j])):
                        diff += abs(differenceVectors[j][k])
                        squareDiff += differenceVectors[j][k]**2
                    # squareDiff = squareDiff**(0.5)
                    diffMeans[j] += diff/nVids
                    sqdiffMeans[j] += squareDiff/nVids
                    # Plotting
                    if plot:
                        ax = fig.add_subplot(len(expertURLs),nAlgs, nAlgs*i + j+1)
                        bars = ax.bar([0,1,2,3,4,5],calibratedVectors[j],color = 'r',alpha = 0.35,label='Student Grades')
                        ax.bar([0,1,2,3,4,5],expertVector,color = 'b', alpha = 0.35,label='Expert Grades')
                        ax.set_ylim([0,12])
                        ax.set_xticks([0.5,1.5,2.5,3.5,4.5,5.5])
                        ax.set_xticklabels([1,2,3,4,5,6])

                        for k in range(len(differenceVectors[j])):
                            ax.text([0.5,1.5,2.5,3.5,4.5,5.5][k],min(calibratedVectors[j][k]+0.3,11),str('%+.2f' % differenceVectors[j][k]),horizontalalignment='center')
                        if j == 0:
                            ax.set_ylabel(expertURLs[i]+'\n\nScore')
                        if i == 0:
                            ax.set_title(algNamesStrings[j]+'\n')
                            if j == 0:
                                ax.legend(bbox_to_anchor=(0.55,0.15))
                        if i == len(expertURLs)-1:
                            ax.set_xlabel('Rubric Item')

                        ax.text(3,12.3,u"∑|∆s|="+str('%.2f' % diff)+u"  ∑∆s^2="+str('%.2f' % squareDiff),horizontalalignment='center')

            if plot:
                plt.savefig('/Users/Scott/Desktop/Lab '+str(labNumber)+' Practice Comparison.png')
        if plot:
            fig = plt.figure(figsize=(2*len(calibratedVectors),15))
            ax = fig.add_subplot(2,1,1)
            ax.bar(range(len(calibratedVectors)),diffMeans,label=u'mean(∑|∆s|)',width=1)
            ax.set_title(u'Mean ∑|∆s| per video')
            ax.set_xticks([])
            ax.set_xticklabels([])
            ax = fig.add_subplot(2,1,2)
            ax.bar(range(len(calibratedVectors)),sqdiffMeans,label=u'mean(∑(∆s)^2)',width=1)
            ax.set_title(u'Mean ∑(∆s)^2 per video')
            ax.set_xticks([num +0.5 for num in range(len(calibratedVectors))])
            ax.set_xticklabels(algNamesStrings,rotation=45)
            plt.savefig('/Users/Scott/Desktop/Algorithm Comparison.png')

        csvWriter.writerow(["Mean sum(abs(diff)):"]+[str('%.2f'%num) for num in diffMeans])
        csvWriter.writerow(["Mean sqrt(sum(diff^2)):"]+[str('%.2f'%num) for num in sqdiffMeans])

for n in [2,3,5,10,20,50]:
    if sample:
        db = SqliteDB("AnonymousCampus.sqlite")
        db.cursor.execute("SELECT DISTINCT URL FROM experts WHERE practice AND URL is not Null")
        expertURLs = [str(entry[0]) for entry in db.cursor.fetchall()]
        for URL in expertURLs:
            if True:
                with open('SampleGrades.csv','w') as csvFile:
                    csvWriter = csv.writer(csvFile, delimiter=',',quotechar='|',quoting=csv.QUOTE_MINIMAL)
                    csvWriter.writerow(['Algorithm',u'sum(delta s)^2 for one video with n='+str(n)+' graders'])


                    data = {}
                    for alg in calibAlgs:
                        print("Sampling "+alg.name)
                        data.update({alg.name:{'sqDiffs':[],'grades':[]}})
                        expertGrade, calibGrades, sqDiffs = getSampleGrades(db,URL,n,N,alg,allCombinations=False)
                        data[alg.name]['sqDiffs']+=sqDiffs
                        data[alg.name]['grades']+=calibGrades
                        csvWriter.writerow([alg.name]+data[alg.name]['sqDiffs'])
            if plot:
                with open('SampleGrades.csv','r') as csvFile:
                    csvReader = csv.reader(csvFile,delimiter=',',quotechar='|')
                    next(csvReader, None)  # skip the first line (header)
                    fig = plt.figure(figsize=(8*len(calibAlgs),7))
                    doOnce = True
                    for row in csvReader:
                        algName = row[0]
                        print("Plotting "+algName+'...')
                        sqDiffs = [float(num) for num in row[1:]]
                        ax = fig.add_subplot(1,len(calibAlgs),algNamesStrings.index(algName)+1)
                        ax.hist(sqDiffs,histtype='step',bins=[i*25 for i in range(20)],label=algName)
                        if doOnce:
                            ax.set_ylabel('Number of Groups')
                            doOnce = False
                        else:
                            ax.set_yticklabels([])
                        ax.set_xlabel(u'∑(∆s)^2')
                        ax.set_title(algName)
                        ax.set_ylim([0,N*len(expertURLs)/32])
                        ax.set_xlim([0,500])
                        ax.text(480,N*len(expertURLs)/32,'mean='+str('%.3f' % mean(sqDiffs))+'\nstDev='+str('%.3f' % std(sqDiffs)),verticalalignment='top',horizontalalignment='right')
                    fig.suptitle(u"Distribution of ∑(∆s)^2 for N="+str(N)+" groups of n="+str(n)+" graders")
                # plt.show()
                plt.savefig('./algfigsGaussian'+getYoutubeID(URL)+' Sample N='+str(N)+' n='+str(n)+'.png')
