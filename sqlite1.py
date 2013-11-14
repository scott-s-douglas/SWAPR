import sqlite3
import os.path
import sys
import random


def makeDatabase(databaseName):
	if databaseName[-3:] != ".db":
		databaseName = databaseName + ".db"
	conn = sqlite3.connect(databaseName)
	conn.commit()
	conn.close()
def listToString(list):
	string = ""
	for i in list:
		string += str(i)+"\t"
	return string[:-1] 

def stringToList(string):
	list = [str(line) for line in string.split('\t')]
	return list

#class for connecting, inserting, and retrieving information from a sqlite3 database
class SqliteDB:
	
	#connects to the database, alters its name if named incorrectly
	def __init__(self, databaseName):
		if databaseName[-3:] != ".db":
			databaseName = databaseName + ".db"
		if os.path.isfile(databaseName):
			self.databaseName = databaseName;
			self.conn = sqlite3.connect(self.databaseName)
			self.cursor = self.conn.cursor()
		else:
			#sees if database name is unique, so it doesn't overwrite anything
			sys.exit("This database does not exist, use the makeDatabase(databaseName) to create it")

	def createTables(self):
		#creates tables if they do not exist
		self.cursor.execute("CREATE TABLE IF NOT EXISTS students (wID text, email text, UNIQUE(wID, email) ON CONFLICT ABORT)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS submissions (labNumber int, wID text, URL text, metadata text, URLsToGrade text)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS uniqueStudentURL (labNumber int, wID text, URL text, UNIQUE(URL) ON CONFLICT ABORT)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS experts (labNumber int, URL text, grade text, hidden int, PRIMARY KEY(labNumber, URL, hidden))")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS responses (labNumber int, URL text, wID text, response text, practice boolean,  PRIMARY KEY(labNumber, URL, response))")	
		self.cursor.execute("CREATE TABLE IF NOT EXISTS questions (labNumber int, questionNumber int, questionWebassignNumber int, practice boolean)")


		weightString = ''
		for i in range(6):
			weightString += ', weight'+str(i+1)+' num'

		self.cursor.execute("CREATE TABLE IF NOT EXISTS weightsBIBI (labNumber int, wID text"+weightString+", weightSum num)")

		self.cursor.execute("CREATE TABLE IF NOT EXISTS rubrics (labNumber int, itemIndex int, itemType text, itemValues text, graded boolean, itemPrompt text)")

		self.cursor.execute("CREATE TABLE IF NOT EXISTS grades(labNumber int, wID text, URL text, finalGrade number, finalGradeVector text, rawGrade number, rawGradeVector text)")



		##check to see if the tables have already been created
		#creates columns in tables for each lab specified
		self.conn.commit()

	#adds a person into the database, works for both new users and existing ones 
	def addEntry(self, wID, URL, labNumber, metadata = None):
		if self.databaseName != None and self.conn != None and self.cursor !=None:
			#If the student did not submit a URL (aka the inputted URL is '')
			if URL == '':
				self.cursor.execute("INSERT INTO submissions VALUES(?,?,?,?,?)", [labNumber, wID, URL,metadata,''])	
			#try putting the student and its URL into the uniqueStudentURL database to check if the URL is unique
			else:	
				try:
					self.cursor.execute("INSERT INTO uniqueStudentURL VALUES (?,?,?)", [labNumber, wID, URL])
					#if there is no error in inserting to a table where URL has to be unique, put it in the actual student database
					self.cursor.execute("INSERT INTO submissions VALUES(?,?,?,?,?)", [labNumber, wID, URL,metadata,''])	
				#if the try fails, that means that the URL is already in the db, duplicate URL found!
				except:
					self.cursor.execute("SELECT wID FROM uniqueStudentURL WHERE URL=?", [URL])
					print "URL: " + URL + " was initially submitted by: " + self.cursor.fetchall()[0][0]
					URL = "DUPLICATEURL"
					self.cursor.execute("INSERT INTO submissions VALUES(?,?,?,?,?)", [labNumber, wID, URL,metadata,''])	
			self.conn.commit()	
	def addEmail(self, wID, email):
		try:
			self.cursor.execute("INSERT INTO students VALUES (?,?,?)", [wID, email])
		except:
			print "wID: " + wID + " or email: " + email + " already in database."

	#retrieves URL for a specific student and specific lab number
	def getURL(self, wID, labNumber):
		
		self.cursor.execute("SELECT URL FROM submissions WHERE labNumber=? AND wID=?", [labNumber, wID])
		URL = self.cursor.fetchone();
		if URL is not None:
			return (URL[0])
		else:
			return None

	def addExpertURL(self, labNumber, URL,  grade, hidden):
		
		self.cursor.execute("SELECT * FROM experts WHERE URL = ?", [URL])
		#adds in a user if not in database already
		presentURL = self.cursor.fetchone()
		if presentURL ==  None:
			self.cursor.execute("INSERT INTO experts VALUES (?, ?, ?, ?)", [labNumber, URL, listToString(grade), hidden])
			self.conn.commit()	
		elif presentURL == URL: 
			print "The URL " + URL + " is already in the expert database"
		else:
			sys.exit("Trying to overrite")

		##find a way to make seperate expert tables for each lab, and then join them together to prevent the staggaring of grades in the excel sheet
		#self.cursor.execute("SELECT * FROM expert WHERE Lab1Grade")
		#print self.cursor.fetchall()
		
		#query = ("SELECT {0} FROM expert WHERE wID
	def getExpertURLs(self, labNumber):
		self.cursor.execute("SElECT URL, grade FROM experts where labNumber=?", [labNumber])
		URLsAndGrades = {}
		for d in self.cursor.fetchall():
			URLsAndGrades[str(d[0])] = stringToList(str(d[1]))
		return URLsAndGrades

	def finalize(self, labNumber, seed, N, MOOC=False):
		##randomize the youtube URLs
		#for each wID
			#put that into the databse under the student ID
		self.cursor.execute("SELECT URL FROM experts WHERE labNumber=? and hidden=0", [labNumber])
		expertURL = [str(d[0]) for d in self.cursor.fetchall()]
		

		# find all the hidden expert videos	
		self.cursor.execute("SELECT URL FROM experts WHERE labNumber=? and hidden=1", [labNumber])
		hiddenURL = [str(d[0]) for d in self.cursor.fetchall()]
		
		#get all the studnet URLs
		self.cursor.execute("SELECT URL from submissions WHERE labNumber=?", [labNumber])
		data = [str(d[0]) for d in self.cursor.fetchall()]
		
		#assign the students whos videos are designated expert graded URLs to grade, and remove them from the URL pool retrieved above
		if len(expertURL) + N + 1 <= len(data):
			pseudoURL = {}
			for d in expertURL:
				#if the expertURL is not in the data list, then it is a video that is not submitted by a student this sem
				#semester, in which case, we skip it
				if d in data:
					self.cursor.execute("SELECT wID FROM submissions WHERE URL=?", [d])
					indice = (data.index(d) + 1) % len(data)
					while data[indice] in expertURL or data[indice] in hiddenURL:
						indice = (indice + 1) % len(data)
					pseudoURL[d] = data[indice]
					data.remove(d)
			for d in hiddenURL:
				if d in data:
					indice = (data.index(d) + 1) % len(data)
					while data[indice] in expertURL or data[indice] in hiddenURL:
						indice = (indice + 1) % len(data)
					pseudoURL[d] = data[indice]
					data.remove(d)

		self.cursor.execute("SELECT wID FROM submissions WHERE labNumber=? and URL is ''", [labNumber])
		noURLSubmitted = [str(d[0]) for d in self.cursor.fetchall()]
		wIDPseudoURL = {}
		if(data.count('') > 0) and not MOOC:
			for d in noURLSubmitted:
				indice = (data.index('') + 1) % len(data)
				while data[indice] == '':
					indice = (indice + 1) % len(data)
				wIDPseudoURL[d] = data[indice]
				data.remove('')
		else:
			while '' in data:
				data.remove('')


		self.cursor.execute("SELECT wID FROM submissions WHERE labNumber=? AND URL=?", [labNumber, "DUPLICATEURL"])
		noURLSubmitted = [str(d[0]) for d in self.cursor.fetchall()]
		if(data.count("DUPLICATEURL") > 0) and not MOOC:
			for d in noURLSubmitted:
				indice = (data.index("DUPLICATEURL") + 1) % len(data)
				while data[indice] == "DUPLICATEURL":
					indice = (indice + 1) % len(data)
				wIDPseudoURL[d] = data[indice]
				data.remove("DUPLICATEURL")
		else:
			while '' in data:
				data.remove('')

		
		#self.cursor.execute(query)

		random.shuffle(data)
		selectFrom = data + data[:N + len(expertURL) + 1]
		if len(pseudoURL.keys()) > 0:
			# params = ("Lab" + str(labNumber) + "URLSToGrade", "Lab" + str(labNumber) + "URL")
			for key in pseudoURL.keys():
				startIndex = selectFrom.index(pseudoURL[key])
				URLSToGrade = selectFrom[startIndex: startIndex+N+1]
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				self.cursor.execute("UPDATE submissions SET URLsToGrade=? WHERE URL=?", [listToString(expertURL + URLSToGrade), key])
				self.conn.commit()
		if len(wIDPseudoURL.keys()) > 0:
			for key in wIDPseudoURL.keys():
				startIndex = selectFrom.index(wIDPseudoURL[key])
				URLSToGrade = selectFrom[startIndex: startIndex+N+1]
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				self.cursor.execute("UPDATE submissions SET URLsToGrade=? WHERE wID=?", [listToString(expertURL + URLSToGrade), key])
				self.conn.commit()
			
		if len(data) > N:
			for d in data:
				startIndex = selectFrom.index(d)
				URLSToGrade = selectFrom[startIndex:startIndex+N+1]
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				# params = ("Lab" + str(labNumber) + "URLSToGrade", "Lab" + str(labNumber) + "URL")
				self.cursor.execute("UPDATE submissions SET URLsToGrade=? WHERE URL=? and labNumber=?", [listToString(expertURL + URLSToGrade), d, labNumber])
		self.conn.commit()
	def getURLsToGrade(self, wID, labNumber):
		self.cursor.execute("Select URLsToGrade FROM submissions WHERE wID=? and labNumber=?", [wID, labNumber])
		dbExtract = self.cursor.fetchone()
		if dbExtract == None:
			return False
		else:
			return [i for i in stringToList(dbExtract[0])]
	
	def addGrade(self, wID, labNumber, URL, grade , practice = False):
		URLsToGrade = self.getURLsToGrade(wID, labNumber)
		if URLsToGrade != False:
			if URL in URLsToGrade:
				self.cursor.execute("INSERT INTO responses VALUES(?, ?, ?, ?, ?)", [labNumber, URL, wID, listToString(grade), practice])
				self.conn.commit()
			else:
				print "wID: " + wID + " was not assigned to grade URL: " + URL
		else:
			print("wID: " + wID + " not in the submissions table")

	def wIDGradesSubmitted(self, wID, labNumber):
		URLsToGrade = self.getURLsToGrade(wID, labNumber)
		gradesSubmitted = {}
		for URL in URLsToGrade:
			self.cursor.execute("SElECT grade FROM grades WHERE wID = ? AND URL = ?",[wID, URL])
			dbExtract = self.cursor.fetchall()
			#if they did not grade the URL assigned to them
			if dbExtract!=[]:
				gradesSubmitted[URL] =  stringToList(str(dbExtract[0][0]))
			else:
				gradesSubmitted[URL] = None
		return gradesSubmitted

	def compareToExpert(self, wID, labNumber):
		expertURLsAndGrades = self.getExpertURLs(labNumber)
		userSubmittedGrades = self.wIDGradesSubmitted(wID, labNumber)
		URLsGraded = userSubmittedGrades.keys()
		for key in expertURLsAndGrades.keys():
			if key in URLsGraded:
				print expertURLsAndGrades[key]
				print userSubmittedGrades[key]	
				
	def getGrades(self, wID, labNumber):
		URL = self.getURL(wID, labNumber)
		self.cursor.execute("SELECT grade,wID FROM grades WHERE URL=?", [URL])
		grades = {}
		for d in self.cursor.fetchall():
			grades[str(d[1])] = str(d[0])
		return grades
	def check(self, labNumber):
		# params = ("Lab" + str(labNumber) + "URL", "Lab" + str(labNumber) + "URLsToGrade", None)
		self.cursor.execute("Select URL, URLsToGrade FROM submissions WHERE URL!= ''")
		fetch = self.cursor.fetchall()
		individualURL = [str(d[0]) for d in fetch]
		URLList = listToString([str(d[1]) for d in fetch])

		for i in range(1, len(individualURL)-1):
			if individualURL[i] not in stringToList(URLList[i]):
				print individualURL[i]
				return False
		return True
		


if False:
	os.remove("test.db")
	makeDatabase("test.db")
	sqldb = SqliteDB("test.db")
	sqldb.createTables()
	sqldb.addEntry("1", "1lkjsdf", 1)
	sqldb.addEntry("2", "1lkjsdf", 1)
	sqldb.addEntry("3", "1lkjsdf", 1)
	sqldb.addEntry("4", "4lkjsdf", 1)
	# sqldb.addEntry("4a",None , 2)
	sqldb.addEntry("5", "5lkjsdf", 1)
	sqldb.addEntry("6", "6lkjsdf", 1)
	sqldb.addEntry("7", "7lkjsdf", 1)
	sqldb.getURL("1", 1)
	sqldb.getURL("2", 1)
	sqldb.addExpertURL(1, "5lkjsdf",[1, 2, 3, 4, 5, 6, 7], 0)
	sqldb.addExpertURL(1, "2lkjsdf", [1, 7, 3, 1, 6, 3], 0)
	# sqldb.addEntry("8", None, 2)
	sqldb.addEntry("8", '', 1)
	sqldb.addEntry(9, "hidden", 1)
	sqldb.addExpertURL(1, "hidden", [1, 2, 3], 1)
	print "testing below"
	sqldb.finalize(1, 1, 3)
	print sqldb.getURLsToGrade("1", 1)
	sqldb.addGrade("1",1,  "5lkjsdf", [1, 2, 3, 4])
	sqldb.addGrade("12",1,  "asdf", 1)
	sqldb.addGrade("1", 1, "2kjla", 1)
	sqldb.addGrade("2", "1", "5lkjsdf", [4, 3, 2, 1])
	sqldb.wIDGradesSubmitted("1", 1)
	sqldb.getGrades("5", 1)
	sqldb.getExpertURLs(1)
	sqldb.compareToExpert("1",1)
	sqldb.check(1)
# sqldb.addExpert("expertVideo", 1, 1)		
# sqldb.addExpert("test2", 2, 2)

