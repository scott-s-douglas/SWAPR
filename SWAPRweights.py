from __future__ import division
from SWAPRsqlite import *
from SWAPRrubric import *
from itertools import groupby

# The "pairs" list contains one entry for each student. Each entry looks like
# [ 'wID' , [ [ [studentResponse0],[expertResponse0] ], [ [studentResponse1],[expertResponse1] ]...  ], [itemIndices] ]

def weightOffset(pairs,scoresDict):
	# Calculate the average difference betwen student/expert response for each item.
	N = len(pairs)	# number of students
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	offsets = []

	# Naively assume that the first pairs entry includes a proper itemIndices list and itemScores list
	itemIndices = pairs[0][2]

	# Get the number of items
	for i in range(N):
		offsets.append(['',[0 for j in range(R)]])
	for i in range(len(pairs)):
		# add student i's wID
		offsets[i][0] = pairs[i][0]
		E = len(pairs[i][1])	# number of response pairs
		for pair in pairs[i][1]:
			studentGrade = pair[0]
			expertGrade = pair[1]
			if len(expertGrade) == len(studentGrade) and len(studentGrade) == R:	# Make sure they're not blank, and are the same length
				for j in range(R):
					# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
					if studentGrade[j] != None:
						# The offset for an item is the average (student - expert) score; when we're calculating grades, we'll need to SUBTRACT this offset from the student score.
						studentScore = scoresDict[itemIndices[j]][studentGrade[j]]
						try:
							expertScore = scoresDict[itemIndices[j]][round(expertGrade[j])]	# Lab 1 had fractional expert grades
						except:
							# print(expertGrade)
							pass
						offsets[i][1][j] += (studentScore-expertScore)/E
	return offsets
				

def weightBIBI(pairs,scoresDict):
	'a.k.a. BIBI_1'
	# BIBI: Binary Item-By-Item
	# Calculate a scalar binary weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	N = len(pairs)	# number of students
	# Get the length of the first set of graded responses; = # of graded rubric items
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	weights = []
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

def weightDIBI_1(pairs,scoresDict):
	'a.k.a. BIBI_0'
	# DIBI: Discrete Item-By-Item
	# Calculate a scalar weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	N = len(pairs)	# number of students
	# Get the length of the first set of graded responses; = # of graded rubric items
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	weights = []
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


def weightDIBI_05(pairs,scoresDict):
	# DIBI: Discrete Item-By-Item (1 if dead on, 0.5 if 1 away from expert response)
	# Calculate a scalar weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	N = len(pairs)	# number of students
	# Get the length of the first set of graded responses; = # of graded rubric items
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	itemIndices = pairs[0][2]
	weights = []
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
				for itemIndex in itemIndices:
					j = itemIndices.index(itemIndex)
					# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
					if studentGrade[j] != None:
						gradeDiff = abs(float(studentGrade[j])-float(expertGrade[j]))
						if gradeDiff <= 0.5:
							weights[i][1][j] += 1/E
						elif 0.5 < gradeDiff <= 1.1:
							weights[i][1][j] += 0.5/E
						else:
							pass
	return weights

def weightCollapseTop2(pairs,scoresDict):
	# Collapse: Collapse top 2 (A, SA) and bottom 2 (SD, D) responses of 5-response rubric items into a single category each; student scores 1/E for responses in the same category as the expert response
	# Calculate a scalar weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	N = len(pairs)	# number of students
	# Get the length of the first set of graded responses; = # of graded rubric items
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	itemIndices = pairs[0][2]
	weights = []
	for i in range(N):
		weights.append(['',[0 for j in range(R)]])
	# print(pairs[0][1][0][0])
	for i in range(len(pairs)):	# Now we do an individual student
		# add the student's wID
		weights[i][0] = pairs[i][0]
		E = len(pairs[i][1])	# number of expert URLs
		for pair in pairs[i][1]:
			# print(pair)
			studentResponse = pair[0]
			expertResponse = pair[1]
			if len(expertResponse) == len(studentResponse) and len(studentResponse) == R:	# Make sure they're not blank, and are the same length
				for itemIndex in itemIndices:
					j = itemIndices.index(itemIndex)
					# Check if this is a 3-response or 5-response rubric item
					# Rubric items are 1-indexed in scoresDict
					if len(scoresDict[itemIndex]) == 5: 
						# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
						if studentResponse[j] != None:
							responseDiff = abs(float(studentResponse[j])-float(expertResponse[j]))
							# Collapse the top and bottom two categories
							if ( 0 < studentResponse[j] < 2 and 0 < expertResponse[j] < 2) or (3 < studentResponse[j] and 3 < expertResponse[j]):
								weights[i][1][j] += 1/E
							# Middle category has to be dead-on
							elif responseDiff < 1 and 2 < expertResponse[j] < 3:
								weights[i][1][j] += 1/E
							else:
								pass
					elif len(scoresDict[itemIndex]) == 3:
						# If this is a 3-response rubric item, then you always have to be dead-on
						if studentResponse[j] != None:
							responseDiff = abs(float(studentResponse[j])-float(expertResponse[j]))
							if responseDiff == 0:
								weights[i][1][j] += 1/E
							else:
								pass

	return weights

def weightCollapseMid3(pairs,scoresDict):
	# Collapse: Collapse middle 3 responses (D, N, A) of 5-response rubric items into a single category; student scores 1/E for responses in the same category as the expert response
	# Calculate a scalar weight for each graded rubric item, then store them in a weight vector
	# Need the ordered pair
	N = len(pairs)	# number of students
	# Get the length of the first set of graded responses; = # of graded rubric items
	R = len(pairs[0][2])	# number of graded rubric items == number of item weights
	itemIndices = pairs[0][2]
	weights = []
	for i in range(N):
		weights.append(['',[0 for j in range(R)]])
	# print(pairs[0][1][0][0])
	for i in range(len(pairs)):	# Now we do an individual student
		# add the student's wID
		weights[i][0] = pairs[i][0]
		E = len(pairs[i][1])	# number of expert URLs
		for pair in pairs[i][1]:
			# print(pair)
			studentResponse = pair[0]
			expertResponse = pair[1]
			if len(expertResponse) == len(studentResponse) and len(studentResponse) == R:	# Make sure they're not blank, and are the same length
				for itemIndex in itemIndices:
					j = itemIndices.index(itemIndex)
					# Check if this is a 3-response or 5-response rubric item
					# Rubric items are 1-indexed in scoresDict
					if len(scoresDict[itemIndex]) == 5: 
						# If the student and expert response for a particular item are within 1 of each other, the student gets 1/N points in that weight coordinate
						if studentResponse[j] != None:
							responseDiff = abs(float(studentResponse[j])-float(expertResponse[j]))
							# Collapse the middle 3 categories
							if ( 1 < studentResponse[j] < 4 and 1 < expertResponse[j] < 4 ):
								weights[i][1][j] += 1/E
							# Top and bottom two categories have to be dead-on
							elif ( (studentResponse[j] <=1 and expertResponse[j] <= 1) or ( studentResponse == 4 and expertResponse == 4) ) :
								weights[i][1][j] += 1/E
							else:
								pass
					elif len(scoresDict[itemIndex]) == 3:
						# If this is a 3-response rubric item, then you always have to be dead-on
						if studentResponse[j] != None:
							responseDiff = abs(float(studentResponse[j])-float(expertResponse[j]))
							if responseDiff == 0:
								weights[i][1][j] += 1/E
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
	responsePairsBywID = []
	# group by wID
	for wID, tempwIDgroup in groupby(data,lambda entry: str(entry[0])):
		responsePairs = []
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
					studentResponses.append(float(entry[2]))
				except:
					studentResponses.append(None)

				try:
					expertResponses.append(float(entry[3]))
				except:
					print('Invalid expert response! URL='+str(URL))
				try:
					itemIndices.append(int(entry[4]))
				except:
					print("Invalid item index: "+str(entry))
					break
			responsePairs.append([studentResponses,expertResponses])

		responsePairsBywID.append([wID,responsePairs,itemIndices])
	# print(responsePairsBywID[0])

	return responsePairsBywID


def assignWeights(db,labNumber,f):
	db.cursor.execute("SELECT responses.wID, responses.URL, responses.response, experts.response, responses.itemIndex FROM responses, experts, rubrics WHERE responses.itemIndex = experts.itemIndex AND responses.itemIndex = rubrics.itemIndex AND rubrics.graded AND rubrics.labNumber = responses.labNumber AND experts.labNumber = responses.labNumber AND responses.labNumber = ? and experts.URL = responses.URL AND experts.labNumber = responses.labNumber AND NOT experts.practice ORDER BY responses.wID, responses.URL, responses.itemIndex",[labNumber])
	pairs = getExpertResponsePairs([entry for entry in db.cursor.fetchall()])
	for entry in f(pairs,getScoresDict(db,labNumber)):
		try:
			wID = entry[0]
			weight = entry[1]
			itemIndices = pairs[0][2]
			for i in range(len(weight)):
				db.cursor.execute("INSERT INTO weights VALUES (NULL,?,?,?,?,?)",[labNumber,wID,f.__name__,itemIndices[i],weight[i]])
		except:
			print('Could not calculate weight for '+wID)
	db.conn.commit()

def assignCalibrationGrades(db,labNumber, nCalibration, likert5only = False):
	'Give each student a calibration grade (out of 100) for each labNumber. Each itemIndex has a maximum weight of 1; there are R weighted (i.e. graded) items per rubric.'
	# First, get R
	R = getNgradedItems(db,labNumber,likert5only)
	if not likert5only:
		db.cursor.execute('''SELECT wID, weightType, sum(weight)
			FROM weights
			WHERE
				labNumber = ?
				AND weight IS NOT NULL
			GROUP BY wID, weightType
			ORDER BY wID, weightType
			''',[labNumber])
	else:
		db.cursor.execute('''SELECT w.wID, w.weightType, sum(w.weight)
			FROM weights w, rubrics r
			WHERE
				w.labNumber = ?
				AND w.labNumber = r.labNumber
				AND w.itemIndex = r.itemIndex
				AND r.itemType = 'likert5'
				AND w.weight IS NOT NULL
			GROUP BY w.wID, w.weightType
			ORDER BY w.wID, w.weightType
			''',[labNumber])
	data = [ [str(entry[0]), str(entry[1]), float(entry[2])] for entry in db.cursor.fetchall() ]
	for wID, wIDgroup in groupby(data, key = lambda x: x[0]):
		for entry in wIDgroup:
			weightType = entry[1]
			rawScore = entry[2]
			grade = 100*rawScore/R
			db.cursor.execute('''INSERT INTO calibrationGrades
				VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
				''',[labNumber, wID, nCalibration, 'likert5' if likert5only else 'all', weightType, rawScore, grade])
	db.conn.commit()