from __future__ import division
from SWAPRsqlite import *
from SWAPRrubric import *
from itertools import groupby

def weightBIBI(pairs):
	# BIBI: Binary Item-By-Item
	# Calculate a scalar binary weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	N = len(pairs)	# number of students
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	weights = []
	# Get the length of the first set of graded responses; = # of graded rubric items
	for i in range(N):
		weights.append(['',[0 for j in range(R)]])
	# print(pairs[0][1][0][0])
	for i in range(len(pairs)):	# Now we do an individual student
		# add the student's wID
		weights[i][0] = pairs[i][0]
		E = len(pairs[i][1])	# number of expert URLs
		for pair in pairs[i][1]:
			# print(pair)
			studentGrade = pair[0]
			expertGrade = pair[1]
			if len(expertGrade) == len(studentGrade) and len(studentGrade) == R:	# Make sure they're not blank, and are the same length
				for j in range(R):
					# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
					if studentGrade[j] != None:
						if abs(float(studentGrade[j])-float(expertGrade[j])) <= 1.1:
							weights[i][1][j] += 1/E
	return weights

def weightDIBI_1(pairs):
	# DIBI: Discrete Item-By-Item
	# Calculate a scalar weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	N = len(pairs)	# number of students
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	weights = []
	# Get the length of the first set of graded responses; = # of graded rubric items
	for i in range(N):
		weights.append(['',[0 for j in range(R)]])
	# print(pairs[0][1][0][0])
	for i in range(len(pairs)):	# Now we do an individual student
		# add the student's wID
		weights[i][0] = pairs[i][0]
		E = len(pairs[i][1])	# number of expert URLs
		for pair in pairs[i][1]:
			# print(pair)
			studentGrade = pair[0]
			expertGrade = pair[1]
			if len(expertGrade) == len(studentGrade) and len(studentGrade) == R:	# Make sure they're not blank, and are the same length
				for j in range(R):
					# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
					if studentGrade[j] != None:
						gradeDiff = abs(float(studentGrade[j])-float(expertGrade[j]))
						if gradeDiff <= 0.5:
							weights[i][1][j] += 1/E
						elif 0.5 < gradeDiff <= 1.1:
							weights[i][1][j] += 0
						else:
							pass
	return weights

def addWeightOld(db,wID,weight,labNumber):
	G = len(weight)
	if G == 6:
		try:
			db.cursor.execute("INSERT INTO weightsBIBI VALUES (NULL,?,?"+G*",?"+",?)",[labNumber, wID, weight[0], weight[1], weight[2], weight[3], weight[4], weight[5], sum(weight)])
		except:
			print("Could not add "+wID+" lab "+str(labNumber)+" weight to database: too many responses. Might be enrolled in more than one section: TA or instructor?")
	elif G == 5:
		# print(weight)
		try:
			db.cursor.execute("INSERT INTO weightsBIBI VALUES (NULL,?,?,?,?,?,?,?,?,?)",[labNumber, wID, weight[0], weight[1], weight[2], weight[3], weight[4], 0, sum(weight)])
		except:
			print("Could not add "+wID+" lab "+str(labNumber)+" weight to database: too many responses. Might be enrolled in more than one section: TA or instructor?")
	# db.conn.commit()

def perform(f, *args):
	# Allow us to pass in another function as an argument, for easily switching out the weighting algorithms
	f(*args)

def getExpertResponsePairs(data):
	gradePairsBywID = []
	# group by wID
	# data.sort(key=lambda entry: str(entry[0]))
	for wID, tempwIDgroup in groupby(data,lambda entry: str(entry[0])):
		gradePairs = []
		wID = str(wID)
		# group by URL
		wIDgroup = list(tempwIDgroup)
		for URL, wIDlist in groupby(wIDgroup, lambda entry: str(entry[1])):
			sortedList = list(wIDlist)
			# print(sortedList)
			studentResponses = []
			expertResponses = []
			itemIndices = []
			for entry in sortedList:
				try:
					itemIndices.append(int(entry[4]))
				except:
					print("Invalid item index: "+str(entry))
					break
				try:
					studentResponses.append(float(entry[2]))
				except:
					studentResponses.append(None)

				try:
					expertResponses.append(float(entry[3]))
				except:
					print('Invalid expert response! URL='+str(URL))
			gradePairs.append([studentResponses,expertResponses])

		gradePairsBywID.append([wID,gradePairs,itemIndices])
	# print(gradePairsBywID[0])

	return gradePairsBywID


def assignWeights(db,labNumber,f):
	db.cursor.execute("SELECT responses.wID, responses.URL, responses.response, experts.response, responses.itemIndex  FROM responses, experts, rubrics WHERE responses.itemIndex = experts.itemIndex AND responses.itemIndex = rubrics.itemIndex AND rubrics.graded AND rubrics.labNumber = responses.labNumber AND experts.labNumber = responses.labNumber AND responses.labNumber = ? and experts.URL = responses.URL AND experts.labNumber = responses.labNumber AND NOT experts.practice ORDER BY responses.wID, responses.URL, responses.itemIndex",[labNumber])
	pairs = getExpertResponsePairs([entry for entry in db.cursor.fetchall()])
	for entry in f(pairs):
		try:
			wID = entry[0]
			weight = entry[1]
			itemIndices = pairs[0][2]
			for i in range(len(weight)):
				db.cursor.execute("INSERT INTO weights VALUES (NULL,?,?,?,?,?)",[labNumber,wID,f.__name__,itemIndices[i],weight[i]])
		except:
			print('Could not calculate weight for '+wID)
	db.conn.commit()

# def assignWeightsBIBI(db,labNumber,f):
def assignWeightsBIBI(pairs):
	# Get all the wIDs of people who turned in grades
	db.cursor.execute("SELECT responses.wID, responses.URL, responses.response, experts.response, responses.itemIndex  FROM responses, experts, rubrics WHERE responses.itemIndex = experts.itemIndex AND responses.itemIndex = rubrics.itemIndex AND rubrics.graded AND rubrics.labNumber = responses.labNumber AND experts.labNumber = responses.labNumber AND responses.labNumber = ? and experts.URL = responses.URL AND experts.labNumber = responses.labNumber AND NOT experts.practice",[labNumber])
	pairs = getExpertResponsePairs([entry for entry in db.cursor.fetchall()])
	# print(pairs)
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