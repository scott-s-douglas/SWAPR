from __future__ import division
from sqlite1 import *
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
						if abs(float(studentGrades[i][j])-float(expertGrades[i][j])) <= 1:
							weight[j] += 1/N
					except:
						# print("Could not calibrate "+str(studentGrades[i])+" with "+str(expertGrades[i]))
						pass
	return weight

def addWeight(db,wID,weight,labNumber):
	G = len(weight)
	db.cursor.execute("INSERT INTO weightsBIBI VALUES (?,?"+G*",?"+",?)",[labNumber, wID, weight[0], weight[1], weight[2], weight[3], weight[4], weight[5], sum(weight)])
	db.conn.commit()
def perform(f, *args):
	# Allow us to pass in another function as an argument, for easily switching out the weighting algorithms
	f(*args)

def assignWeightsBIBI(db,labNumber,f):
	# Get all the wIDs of people who turned in grades
	db.cursor.execute("SELECT wID FROM student")
	wIDs = set([str(d[0]) for d in db.cursor.fetchall()])
	for wID in wIDs:
		db.cursor.execute("SELECT wID, grades.grade, expert.grade, grades.URL FROM grades, expert WHERE grades.URL = expert.URL AND grades.labNumber = ? AND expert.labNumber = ? AND NOT grades.practice AND wID = ?",[labNumber,labNumber,wID])
		studentGradesTemp = []
		expertGrades = []
		data = db.cursor.fetchall()
		if len(data) > 0:
			for d in data:
				studentGradesTemp.append( stringToList( str( d[1] ) ) )
				expertGrades.append( stringToList( str( d[2] ) ) )
			
			# Now we need to strip out the ungraded items from the studentGrades
			gradedDict = getRubricGradedDict(db,labNumber)
			studentGrades = []
			for tempGrade in studentGradesTemp:
				grade = []
				for i in range(len(tempGrade)):
					if gradedDict[i+1]:	# Items in the db are 1-indexed
						grade.append(tempGrade[i])
				studentGrades.append(grade)

			weight = f(studentGrades,expertGrades)
			# print("Calculating weight for "+wID+"...")
			addWeight(db,wID,weight,labNumber)
		else:
			addWeight(db,wID,[0,0,0,0,0,0],labNumber)


def createWeightsTableBIBI(db,G=6):
	# BIBI: Binary Item-By-Item
	weightString = ''
	for i in range(G):
		weightString += ', weight'+str(i+1)+' num'

	db.cursor.execute("CREATE TABLE IF NOT EXISTS weightsBIBI (labNumber int, wID text"+weightString+", weightSum num)")
# Import student grades from database, import expert grades to the database, calculate item-by-item weights