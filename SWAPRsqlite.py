import sqlite3
import os.path
import sys
import random
import glob


def makeDatabase(databaseName):
	if databaseName[-7:] != ".sqlite":
		databaseName = databaseName + ".sqlite"
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
def listdir_nohidden(path):
	# Return only the non-hidden files in a directory, to avoid that annoying .DS_Store file
	return glob.glob(os.path.join(path, '*'))

#class for connecting, inserting, and retrieving information from a sqlite3 database
class SqliteDB:
	
	#connects to the database, alters its name if named incorrectly
	def __init__(self, databaseName):
		if databaseName[-7:] != ".sqlite":
			databaseName = databaseName + ".sqlite"
		if os.path.isfile(databaseName):
			self.databaseName = databaseName;
			self.conn = sqlite3.connect(self.databaseName)
			self.cursor = self.conn.cursor()
		else:
			#sees if database name is unique, so it doesn't overwrite anything
			sys.exit("This database does not exist, use the makeDatabase(databaseName) to create it")

	def createTables(self):
		#creates tables if they do not exist
		self.cursor.execute("CREATE TABLE IF NOT EXISTS students (row INTEGER PRIMARY KEY NOT NULL, fullName unicode, wID text, email text, UNIQUE(wID, email) UNIQUE(fullName, email) ON CONFLICT ABORT)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS submissions (row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text, URL text, metadata text)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS assignments (row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text, questionIndex int, URL text)")
		# self.cursor.execute("CREATE TABLE IF NOT EXISTS uniqueStudentURL (labNumber int, wID text, URL text, UNIQUE(URL) ON CONFLICT ABORT)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS experts (row INTEGER PRIMARY KEY NOT NULL, labNumber int, URL text, itemIndex int, response text, hidden boolean, practice boolean)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS responses (row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text, wQuestion int, URL text, itemIndex int, response text)")        
		self.cursor.execute("CREATE TABLE IF NOT EXISTS questions (row INTEGER PRIMARY KEY NOT NULL, labNumber int, questionIndex int, wQuestion int, practice boolean)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS rubrics (row INTEGER PRIMARY KEY NOT NULL, labNumber int, itemIndex int, itemType text, itemPrompt text, graded boolean)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS responseKeys (row INTEGER PRIMARY KEY NOT NULL, labNumber int, itemIndex int, response int, score number)")


		# weightString = ''
		# for i in range(6):
		# 	weightString += ', weight'+str(i+1)+' num'

		# self.cursor.execute("CREATE TABLE IF NOT EXISTS weightsBIBI (row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text"+weightString+", weightSum num)")

		self.cursor.execute("CREATE TABLE IF NOT EXISTS weights(row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text, weightType text, itemIndex int, weight number)")

		self.cursor.execute("CREATE TABLE IF NOT EXISTS itemGrades(row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text, URL text, itemIndex int, rawScore number, grade number, calibrated boolean)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS finalGrades(row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text, URL text, rawScore number, grade number, calibrated boolean)")



		##check to see if the tables have already been created
		#creates columns in tables for each lab specified
		self.conn.commit()

	#adds a person into the database, works for both new users and existing ones 
	def addSubmission(self, wID, URL, labNumber, metadata = None):
		if self.databaseName != None and self.conn != None and self.cursor !=None:
			self.cursor.execute("INSERT INTO submissions VALUES(?,?,?,?,?)", [None,labNumber, wID, URL ,metadata])        
			# self.conn.commit()        
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

	def addExpertURL(self, labNumber, URL, itemIndex, response, hidden, practice):
		
		# self.cursor.execute("SELECT * FROM experts WHERE URL = ?", [URL])
		#adds in a user if not in database already
		self.cursor.execute("INSERT INTO experts VALUES (NULL, ?, ?, ?, ?, ?, ?)", [labNumber, URL, itemIndex, response, hidden, practice])
		self.conn.commit()        

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
		self.cursor.execute("SELECT URL, hidden FROM experts WHERE labNumber=?", [labNumber])
		expertURL = []
		hiddenURL = []
		for d in self.cursor.fetchall():
			if d[1] == 1:
				hiddenURL.append(str(d[0]))
			elif d[1] == 0:
				expertURL.append(str(d[0]))
		
		#deprecated code, due to its slowness
		#self.cursor.execute("SELECT URL FROM experts WHERE labNumber=? and hidden=0", [labNumber])
		#expertURL = [str(d[0]) for d in self.cursor.fetchall()]
		

		# find all the hidden expert videos
		#self.cursor.execute("SELECT URL FROM experts WHERE labNumber=? and hidden=1", [labNumber])
		#hiddenURL = [str(d[0]) for d in self.cursor.fetchall()]
	   
		#get all the studnet URLs
		self.cursor.execute("SELECT wID, URL from submissions WHERE labNumber=?", [labNumber])
		data = []
		URLTowIDDict = {}
		pseudoURL = {}
		for d in self.cursor.fetchall():
			data.append(str(d[1]))
			URLTowIDDict[str(d[1])] = str(d[0])
		print "original data size", len(data)
		
		#assign the students whos videos are designated expert graded URLs to grade, and remove them from the URL pool retrieved above
		if len(expertURL) + N + 1 <= len(data):
			for d in expertURL:
				#if the expertURL is not in the data list, then it is a video that is not submitted by a student this sem
				#semester, in which case, we skip it
				if d in data:
					#self.cursor.execute("SELECT wID FROM submissions WHERE URL=?", [d])
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
				for i in range(0, len(URLSToGrade)):
					#i+1 because we want item index to start at 1
					self.cursor.execute("INSERT INTO assignments VALUES(NULL, ?, ?, ?, ?)", [labNumber, key, i+1, URLSToGrade[i]])
				self.conn.commit()
		if len(wIDPseudoURL.keys()) > 0:
			for key in wIDPseudoURL.keys():
				startIndex = selectFrom.index(wIDPseudoURL[key])
				URLSToGrade = selectFrom[startIndex: startIndex+N+1]
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				for i in range(0, len(URLSToGrade)):
					#i+1 because we want item index to start at 1
					self.cursor.execute("INSERT INTO assignments VALUES(NULL, ?, ?, ?, ?)", [labNumber, key, i+1, URLSToGrade[i]])
				self.conn.commit()
		if len(data) > N:
			for d in data:
				startIndex = selectFrom.index(d)
				URLSToGrade = selectFrom[startIndex:startIndex+N+1]
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				# params = ("Lab" + str(labNumber) + "URLSToGrade", "Lab" + str(labNumber) + "URL")
				# self.cursor.execute("UPDATE submissions SET URLsToGrade=? WHERE URL=? and labNumber=?", [listToString(expertURL + URLSToGrade), d, labNumber])

				for i in range(0, len(URLSToGrade)):
					#i+1 because we want item index to start at 1
					self.cursor.execute("INSERT INTO assignments VALUES(NULL, ?, ?, ?, ?)", [labNumber, URLTowIDDict[d], i+1, URLSToGrade[i]])
		self.conn.commit()
		
##############################################################################################################
		#will comment out once these conditions are met, due to some issues with encrypting URLs due to FERPA.
##############################################################################################################
		#checks to see if each URL was assigned >4 times
		self.cursor.execute("SELECT URL from assignments")
		
		#checks is the URLs in the Assignment table
		checks = [str(d[0]) for d in self.cursor.fetchall()]


		print "-sanity checks, checks to see if URL was assigned more than N+1 or less than N"
		for URL in set(checks):
			if checks.count(URL)>N+1:                        
				print checks.count(URL), URL, data.count(URL), "->num of times assigned, URL, number of times submitted, respectively"
			elif checks.count(URL) < N:
				print checks.count(URL), URL, data.count(URL), "->num of times assigned, URL, number of times submitted, respectively"
		print "-end of checks to see if URL was assigned the correct number of times"
		#is the # of times that hiddenURL is assigned the same as submissions?
		for item in set(data):
			if item not in checks:
				print item + " not in checks"
		print "length of set(checks) vs length of checks:", len(set(checks)), len(checks)
		print "length of set(data) vs length of data:", len(set(data)), len(data)
		dictThings = [URLTowIDDict[d] for d in URLTowIDDict.keys()]
		for i in dictThings:
			if dictThings.count(i)>1:
				print i, "is in URLtowIDDict more than once"
		#print hiddenURL 
		#print checks.count(hiddenURL[0])
		self.cursor.execute("SELECT wID FROM submissions WHERE labNumber=3")
		print "number of unique wIDs in submissions:", len(set(self.cursor.fetchall()))
		self.cursor.execute("SELECT wID FROM assignments")
		print "number of unique wIDs in assignments:", len(set(self.cursor.fetchall()))
##########################################################################################################
	

	def getURLsToGrade(self, wID, labNumber):
		self.cursor.execute("Select URL FROM assignments WHERE wID=? and labNumber=? ORDER BY questionIndex", [wID, labNumber])
		dbExtract = [entry for entry in self.cursor.fetchall()]
		if dbExtract == []:
			return False
		else:
			return [str(i[0]) for i in dbExtract]
	
	def addResponse(self, labNumber, wID, wQuestion, itemIndex, response):
		self.cursor.execute("INSERT INTO responses VALUES(NULL, ?, ?, ?, ?, ?)", [labNumber, wID, wQuestion, itemIndex, response])
		self.conn.commit()

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
		
