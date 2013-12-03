from SWAPRsqlite import *
import random

def assignURLs(db,labNumber,Npeer):
	# quick and dirty assignment algorithm for Lab 5, doesn't handle the case where a student's URL is used as an expert URL for the same lab
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

	for i in range(len(submissionList)):
		URLsToGrade = [submissionList[i][1]]	# adds the student's own URL
		wID = submissionList[i][0]
		for j in range(Npeer):
			URLsToGrade.append(submissionList[(i+j+1)%len(submissionList)][1]) # add the next Npeer URLs, wrapping around to the beginning of the list. Will fail if len(submissionList) <= Npeer
		for URL in hiddenList:
			URLsToGrade.append(URL)
		random.shuffle(URLsToGrade)
		for j in range(len(URLsToGrade)):
			db.cursor.execute("INSERT INTO assignments VALUES (NULL, ?, ?, ?, ?)",[labNumber,wID,j+1,URLsToGrade[j]])
	db.conn.commit()
