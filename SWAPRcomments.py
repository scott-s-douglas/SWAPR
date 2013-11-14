from sqlite1 import *
from SWAPRrubric import *

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


		# Write the comments report
		typeDict = getRubricTypeDict(db,labNumber)

		db.cursor.execute("SELECT wID FROM submissions where labNumber = ?",[labNumber])
		wIDs = [str(d[0]) for d in db.cursor.fetchall()]



		for wID in wIDs:
			# Get the student's peers' comments
			peerComments = []
			db.cursor.execute("SELECT response FROM responses, submissions WHERE submissions.URL = responses.URL AND submissions.wID = ? and submissions.labNumber = ?",[wID, labNumber])

			responses = [stringToList(str(d[0])) for d in db.cursor.fetchall()]
			if len(responses) > 0:
				for response in responses:
					comments = [str(item).replace('"',"'") for item in response if typeDict[response.index(item) +1] == 'freeResponse'] # Everything in the database is 1-indexed
					peerComments.append(comments)


			# Get the student's URL
			db.cursor.execute("SELECT URL FROM submissions WHERE wID = ? AND labNumber = ?",[wID,labNumber])
			d = db.cursor.fetchone()
			URL = None
			if d is not None:
				URL = str(d[0])

			# Get the student's weights
			db.cursor.execute("SELECT weight1, weight2, weight3, weight4, weight5, weight6 FROM weightsBIBI WHERE wID = ? and labNumber = ?",[wID, labNumber])
			weights = [[float(d[i]) for i in range(6)] for d in db.cursor.fetchall()]
			
			# Get the rubric prompts
			db.cursor.execute("SELECT itemPrompt FROM rubrics WHERE itemType = 'freeResponse' and labNumber = ?",[labNumber])
			prompts = [str(item[0]) for item in db.cursor.fetchall()]

			# Get the student's grade vector
			db.cursor.execute("SELECT finalGradeVector FROM grades WHERE wID = ? and labNumber = ?",[wID, labNumber])
			gradeVector = [stringToList(str(item[0])) for item in db.cursor.fetchall()]
			if gradeVector == []:
				gradeVector = [0,0,0,0,0,0]
			else:
				gradeVector = [float(entry) for entry in gradeVector[0]]

			# Get email, if appropriate
			if writeEmails:
				hasEmail = checkEmail(db,wID)
				if hasEmail:
					db.cursor.execute("SELECT email FROM students WHERE wID = ?",[wID])
					email = str(db.cursor.fetchone()[0])
				# print(email)

			dataString = wID.split('@')[0]
			if writeEmails:
				dataString += '\t'
				if hasEmail:
					try:
						dataString += email
					except:
						pass
			dataString += '\t'
			if URL is not None:
				dataString += URL
			for i in range(6):
				iComments = ''
				if len(peerComments) > 0:
					for comment in peerComments:
						iComments += comment[i]+'; '
					dataString += '\t'+prompts[i]+'\t'+str(gradeVector[i])+'\t'+iComments
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
				db.cursor.execute("INSERT INTO students (wID, email) VALUES (?,?)",[email.split('@')[0]+'@gatech', email ])
	db.conn.commit()

# publicdb = SqliteDB("public.db")
# createEmailsTable(publicdb)
# parseEmails(publicdb,'/Users/Scott/Downloads/Coursera Mail Merge/Emails.csv')
# writeCommentsTabDelimited(publicdb,'Lab1CommentsMOOC.txt',1,writeEmails = True)