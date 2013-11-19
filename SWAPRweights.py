from __future__ import division
from SWAPRsqlite import *
from SWAPRrubric import *
from itertools import groupby

def weightBIBI(pairs):
	# BIBI: Binary Item-By-Item
	# Calculate a scalar binary weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	weight = 6*[0]
	N = len(pairs)
	for pair in pairs:
		studentGrade = pair[0]
		expertGrade = pair[1]
		if len(expertGrade) == len(studentGrade) >= 1:	# Make sure they're not blank, and are the same length
			for i in range(len(studentGrade)):
				# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
				if studentGrade[i] != None:
					if abs(float(studentGrade[i])-float(expertGrade[i])) <= 1.1:
						weight[i] += 1/N
	return weight

def weightDIBI(studentGrades,expertGrades):
	# BIBI: Binary Item-By-Item
	# Calculate a scalar binary weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	weight = 6*[0]
	if len(studentGrades) >= 1 and len(expertGrades) >=1:	# Make sure they're not blank
		N = len(studentGrades)
		doOnce = True
		for i in range(N):	# We loop over all the student/expert video pairs
			if len(expertGrades[i]) == len(studentGrades[i]):
				R = len(studentGrades[i])
				if doOnce:	# Make the weight vector the right length only if we get this far
					weight = R*[0]
					doOnce = False
				for j in range(R):
					# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
					try:
						if abs(int(studentGrades[i][j])-int(expertGrades[i][j])) == 0:
							weight[j] += 1/N
						elif abs(int(studentGrades[i][j])-int(expertGrades[i][j])) == 1:
							weight[j] += 0.8/N
						elif abs(int(studentGrades[i][j])-int(expertGrades[i][j])) == 2:
							weight[j] += 1/N
					except:
						# print("Could not calibrate "+str(studentGrades[i])+" with "+str(expertGrades[i]))
						pass
	return weight

def addWeight(db,wID,weight,labNumber):
	G = len(weight)
	try:
		db.cursor.execute("INSERT INTO weightsBIBI VALUES (NULL,?,?"+G*",?"+",?)",[labNumber, wID, weight[0], weight[1], weight[2], weight[3], weight[4], weight[5], sum(weight)])
	except:
		print("Could not add "+wID+" lab "+str(labNumber)+" weight to database: too many responses. Might be enrolled in more than one section: TA or instructor?")
	# db.conn.commit()
def perform(f, *args):
	# Allow us to pass in another function as an argument, for easily switching out the weighting algorithms
	f(*args)

def getExpertResponsePairs(data):
	gradePairsBywID = []
	# sort by wID, then group by wID
	data.sort(key=lambda entry: str(entry[0]))
	for wID, tempwIDgroup in groupby(data,lambda entry: str(entry[0])):
		gradePairs = []
		wID = str(wID)
		# sort by URL, then group by URL
		wIDgroup = sorted(list(tempwIDgroup),key = lambda x: str(x[1]))
		for URL, wIDlist in groupby(wIDgroup, lambda entry: str(entry[1])):
			sortedList = sorted(list(wIDlist),key=lambda x: x[-1])
			# print(len(sortedList))
			studentResponses = []
			expertResponses = []
			for entry in sortedList:
				try:
					studentResponses.append(float(entry[2]))
				except:
					studentResponses.append(None)

				try:
					expertResponses.append(float(entry[3]))
				except:
					print('Invalid expert response! URL='+str(URL))
			gradePairs.append([studentResponses,expertResponses])

		gradePairsBywID.append([wID,gradePairs])

	return gradePairsBywID




def assignWeightsBIBI(db,labNumber,f):
	# Get all the wIDs of people who turned in grades
	db.cursor.execute("SELECT responses.wID, responses.URL, responses.response, experts.response, responses.itemIndex  FROM responses, experts, rubrics WHERE responses.itemIndex = experts.itemIndex AND responses.itemIndex = rubrics.itemIndex AND rubrics.graded AND rubrics.labNumber = responses.labNumber AND experts.labNumber = responses.labNumber AND responses.labNumber = ? and experts.URL = responses.URL AND experts.labNumber = responses.labNumber AND NOT experts.practice",[labNumber])
	pairs = getExpertResponsePairs([entry for entry in db.cursor.fetchall()])
	for pair in pairs:
		# print(pair)
		# get every pair of expert/student responses from the calibration videos
		wID = pair[0]
		weight = f(pair[1])
		# print("Calculating weight for "+wID+"...")
		addWeight(db,wID,weight,labNumber)
	db.conn.commit()


def createWeightsTableBIBI(db,G=6):
	# BIBI: Binary Item-By-Item
	weightString = ''
	for i in range(G):
		weightString += ', weight'+str(i+1)+' num'

	db.cursor.execute("CREATE TABLE IF NOT EXISTS weightsBIBI (labNumber int, wID text"+weightString+", weightSum num)")
# Import student grades from database, import expert grades to the database, calculate item-by-item weights