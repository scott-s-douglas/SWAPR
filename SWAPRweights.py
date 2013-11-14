from __future__ import division
from SWAPRsqlite import *
from SWAPRrubric import *

def weightBIBI(studentGrades,expertGrades):
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
						if abs(float(studentGrades[i][j])-float(expertGrades[i][j])) <= 1.1:
							weight[j] += 1/N
					except:
						# print("Could not calibrate "+str(studentGrades[i])+" with "+str(expertGrades[i]))
						pass
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
	db.cursor.execute("INSERT INTO weightsBIBI VALUES (NULL,?,?"+G*",?"+",?)",[labNumber, wID, weight[0], weight[1], weight[2], weight[3], weight[4], weight[5], sum(weight)])
	# db.conn.commit()
def perform(f, *args):
	# Allow us to pass in another function as an argument, for easily switching out the weighting algorithms
	f(*args)

def getExpertResponsePairs(db,wID,labNumber):
	db.cursor.execute("SELECT experts.URL FROM experts, responses WHERE wID = ? and experts.URL = responses.URL AND experts.labNumber = responses.labNumber AND experts.labNumber = ? AND NOT experts.practice",[wID, labNumber])
	URLs = [str(entry[0]) for entry in db.cursor.fetchall()]
	URLs = [URL for URL in set(URLs)]	# TODO: make sqlite do this for us
	# print(URLs)
	gradePairs = []
	for URL in URLs:
		db.cursor.execute("SELECT responses.response, experts.response, responses.itemIndex FROM responses, experts, rubrics WHERE responses.itemIndex = experts.itemIndex AND responses.itemIndex = rubrics.itemIndex AND rubrics.graded AND responses.URL = experts.URL AND responses.URL = ? AND responses.wID = ? AND rubrics.labNumber = responses.labNumber AND experts.labNumber = responses.labNumber AND responses.labNumber = ?",[URL,wID,labNumber])
		data = {}
		for entry in db.cursor.fetchall():
			try:
				itemIndex = int(entry[2])
			except:
				print('Invalid item index: wID='+wID+', URL='+URL+', entry='+entry)
			try:
				studentResponse = int(entry[0])
			except:
				studentResponse = None
			try:
				expertResponse = float(entry[1])
			except:
				print('Invalid expert response: URL='+URL)
			data.update( { itemIndex: [ studentResponse, expertResponse ] } )
		# print(db.cursor.fetchone())
		studentFullResponse = []
		expertFullResponse = []
		for i in sorted(data.keys()):
			# Now we get the vector comprising every student response to that URL ordered by itemIndex
			studentFullResponse.append(data[i][0])
			# ...and the expert response
			expertFullResponse.append(data[i][1])

		gradePairs.append([studentFullResponse,expertFullResponse])
	return gradePairs




def assignWeightsBIBI(db,labNumber,f):
	# Get all the wIDs of people who turned in grades
	db.cursor.execute("SELECT wID FROM submissions")
	wIDs = set([str(d[0]) for d in db.cursor.fetchall()])
	for wID in wIDs:
		# get every pair of expert/student responses from the calibration videos
		pairs = getExpertResponsePairs(db,wID,labNumber)
		studentGrades = [pair[0] for pair in pairs]
		expertGrades = [pair[1] for pair in pairs]
		weight = f(studentGrades,expertGrades)
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