from SWAPRsqlite import *
import random

def assignURLs(db,labNumber,Npeer):
	# construct a list of all wID, URL pairs for every submission in this lab, ordered by URL (this ends up being pseudorandom)
	db.cursor.execute("SELECT DISTINCT wID, URL FROM submissions WHERE labNumber = ? AND URL IS NOT NULL ORDER BY URL",[labNumber])
	submissionList = [[str(entry[0]),str(entry[1])] for entry in db.cursor.fetchall()]

	# practice expert URLs
	db.cursor.execute("SELECT DISTINCT URL FROM experts WHERE labNumber = ? AND NOT hidden AND practice",[labNumber])
	practiceList = [str(entry[0]) for entry in db.cursor.fetchall()]

	# expert URLs to be presented as calibration URLs
	db.cursor.execute("SELECT DISTINCT URL FROM experts WHERE labNumber = ? AND NOT hidden AND NOT practice",[labNumber])
	shownList = [str(entry[0]) for entry in db.cursor.fetchall()]

	# expert URLs to be hidden among the peer URLs
	db.cursor.execute("SELECT DISTINCT URL FROM experts WHERE labNumber = ? AND hidden",[labNumber])
	hiddenList = [str(entry[0]) for entry in db.cursor.fetchall()]

	# URL assignment for every student who submitted a video
	for i in range(len(submissionList)):
		URLsToGrade = []
		wID = submissionList[i][0]

		# add all the hidden expert URLs
		for URL in hiddenList:
			URLsToGrade.append(URL)

		j = 0
		while len(URLsToGrade) < Npeer + len(hiddenList) + 1: # the +1 is for the student's own video
			# add the student's own URL and the next Npeer URLs, wrapping around to the beginning of the list, skipping over URLs when they're already present in URLsToGrade. Will fail if len(submissionList) <= Npeer
			thisURL = submissionList[(i+j)%len(submissionList)][1]
			if thisURL not in URLsToGrade:
				URLsToGrade.append(submissionList[(i+j)%len(submissionList)][1])
			else:
				j += 1
			j += 1

		random.shuffle(URLsToGrade)

		# add the practice and then the shown URLs, in order, at the beginning
		URLsToGrade = practiceList + shownList + URLsToGrade

		for j in range(len(URLsToGrade)):
			db.cursor.execute("INSERT INTO assignments VALUES (NULL, ?, ?, ?, ?)",[labNumber,wID,j+1,URLsToGrade[j]])
	# repeat the last set of URLsToGrade as the default set for students who didn't submit a video.
	for j in range(len(URLsToGrade)):
		db.cursor.execute("INSERT INTO assignments VALUES (NULL, ?, ?, ?, ?)",[labNumber,'default',j+1,URLsToGrade[j]])
	db.conn.commit()
