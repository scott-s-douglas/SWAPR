from SWAPRsqlite import *
from SWAPRrubric import *
from itertools import groupby

def writeCommentsTabDelimited(db,filename,labNumber,writeEmails = False):
	with open(filename,'w') as output:
		labelString = "Username"
		if writeEmails:
			labelString += "\tEmail"
		labelString += "\tURL"
		for i in range(6):
			labelString+="\tItem "+str(i+1)+"\tItem "+str(i+1)+" Grade\tItem "+str(i+1)+" Comments\tItem "+str(i+1)+" Calibration"
		labelString += "\n"
		output.write(labelString)


		db.cursor.execute("SELECT wID, URL FROM submissions where labNumber = ?",[labNumber])
		data = db.cursor.fetchall()
		wIDURLpairs = [[str(d[0]),str(d[1])] for d in data]
		totalLength = len(wIDURLpairs)
		currentEntry = 0

		# Get the list of item prompts
		db.cursor.execute("SELECT itemPrompt FROM rubrics WHERE labNumber = ? AND itemType = 'freeResponse' AND itemIndex != 14 ORDER BY itemIndex",[labNumber])
		prompts = [str(prompt[0]) for prompt in db.cursor.fetchall()]

		for pair in wIDURLpairs:
			print(str(currentEntry)+'/'+str(totalLength))
			currentEntry += 1
			wID = pair[0]
			URL = pair[1]
			# Get the student's peers' comments
			peerComments = []
			db.cursor.execute("SELECT responses.itemIndex, response FROM responses, submissions, rubrics WHERE submissions.URL = responses.URL AND submissions.wID = ? and submissions.labNumber = ? AND responses.labNumber = submissions.labNumber AND rubrics.labNumber = submissions.labNumber AND rubrics.itemIndex = responses.itemIndex AND rubrics.itemType = 'freeResponse' AND responses.itemIndex != 14 ORDER BY responses.itemIndex",[wID, labNumber])
			data = [[int(entry[0]),str(entry[1])] for entry in db.cursor.fetchall() if entry[1] != None]
			# print(data)
			# 5/0
			# group by itemIndex
			peerComments = []
			# print(peerComments)
			for itemIndex, itemResponses in groupby(data,key = lambda x: x[0]):
				# print(list(itemResponses))
				iString = ''
				for response in list(itemResponses):
					iString += str(response[1])+'; '
				peerComments.append(iString)
			# print(peerComments)
			# print(peerComments)
			# Get the student's weights
			db.cursor.execute("SELECT weight1, weight2, weight3, weight4, weight5, weight6 FROM weightsBIBI WHERE wID = ? and labNumber = ?",[wID, labNumber])
			weights = [[float(d[i]) for i in range(6)] for d in db.cursor.fetchall()]

			# Get the student's grade vector
			db.cursor.execute("SELECT grade FROM itemGrades, rubrics WHERE wID = ? and itemGrades.labNumber = ?  AND rubrics.labNumber = itemGrades.labNumber AND itemGrades.itemIndex = rubrics.itemIndex AND graded ORDER BY itemGrades.itemIndex",[wID, labNumber])
			gradeVector = [item for item in db.cursor.fetchall()]
			if gradeVector == []:
				gradeVector = [0,0,0,0,0,0]
			else:
				gradeVector = [float(entry[0]) for entry in gradeVector]

			# Get email, if appropriate
			if writeEmails:
				hasEmail = checkEmail(db,wID)
				if hasEmail:
					db.cursor.execute("SELECT email FROM students WHERE wID = ?",[wID])
					email = str(db.cursor.fetchone()[0])
				# print(email)
			dataString = ''
			if writeEmails:
				if hasEmail:
					try:
						dataString += email
						dataString += '\t'
					except:
						dataString += '\t'
			dataString += wID.split('@')[0]
			dataString += '\t'
			if URL is not None:
				dataString += URL
			for i in range(6):
				iComments = ''
				if len(peerComments) > 0:
					# for comment in peerComments:
					# print(peerComments)
					# 	iComments += comment[i]+'; '
					dataString += '\t'+prompts[i]+'\t'+str(gradeVector[i])+'\t'+peerComments[i]
				else:
					dataString += '\t'+prompts[i]+'\t'+str(gradeVector[i])+'\t'+''
				try:
					dataString += '\t'+str(weights[0][i]*3)
				except:
					dataString += '\t'+''
			dataString+='\n'

			output.write(dataString)

def checkEmail(db,wID):
	db.cursor.execute("SELECT email FROM students WHERE wID = ?",[wID])
	result = [item for item in db.cursor.fetchall()]
	if len(result) == 0:
		# print("No matching email for "+wID)
		return False
	elif len(result) > 1:
		print("Ambiguous results for "+wID)
		return False
	else:
		print("Found email for "+wID+': '+str(result[0][0]))
		return True

def parseEmails(db,emailsFile):
	# Read in a .csv file which has student email addresses, put the email addresses in a table
	with open(emailsFile,'r') as emails:
		for email in emails:
			# print(email.split(',')[2].replace('\n',''))
			email = email.split('\t')[1].replace('\n','')
			if len(email) >= 5:
				db.cursor.execute("INSERT INTO students (wID, email) VALUES (NULL,?,?)",[email.split('@')[0]+'@gatech', email ])
	db.conn.commit()

# publicdb = SqliteDB("public.db")
# createEmailsTable(publicdb)
# parseEmails(publicdb,'/Users/Scott/Downloads/Coursera Mail Merge/Emails.csv')
# writeCommentsTabDelimited(publicdb,'Lab1CommentsMOOC.txt',1,writeEmails = True)