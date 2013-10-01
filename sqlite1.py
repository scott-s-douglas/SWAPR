import sqlite3
import os.path
import sys
import pickle
import random

from SWAPRstrings import *

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
# print listToString([1,2,3,4,5])

def stringToList(string):
	list = [str(line) for line in string.split('\t')]
	return list
# print stringToList("1,2,3,4,5")

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

##this code was previous code that probably won't be used, as they were just for testing purposes
##they all were integrated above into the __init__ function
	
	##checks if the database is physically connected to a database, but not a specific one
	##NOT USED IN ANY OF THE CODE BELOW
	#def isConnected(self):
	#	if os.path.isfile(self.databaseName) and self.conn != null and self.cursor !=None:
	#		return True
	#	return False

#	def setDatabaseName(self, databaseName):
#		if databaseName != None:
#			print "There is already a database set"
#			sys.exit("This already points to a database")
#		elif not databaseName[-3:] == ".db":
#			self.databaseName = databaseName + ".db"
#		else:
#			self.databaseName = databaseName
#	def connectToDatabase(self):
#		if os.path.isfile("./" +self.databaseName):
#			self.conn = sqlite3.connect(self.databaseName)
#			self.cursor = self.conn.cursor()
#			
#		else:
#			print self.databaseName + "does not exist"
#			if self.databaseName == None:
#				print "Database name has not been initialized"
	#for brand new semesters, initializes the tables and the lab numbers. !!!!will add more work to add labs to an existing database
	def createTables(self, numLabs = 0):
		#creates tables if they do not exist
		self.cursor.execute("CREATE TABLE IF NOT EXISTS student (wId text, weight num)")
		#SQLite does not support empty tables...
		self.cursor.execute("CREATE TABLE IF NOT EXISTS expert (labNumber int)")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS grades (labNumber int, URL text, wID text, grade text, practice boolean, PRIMARY KEY(labNumber, URL, grade))")	

		##check to see if the tables have already been created
		#creates columns in tables for each lab specified
		for i in range(1, numLabs+1):
			lab = "Lab" + str(i)
			try:
				self.cursor.execute("Alter Table student ADD Column '%s' text" % (lab + "URL"))
				self.cursor.execute("Alter Table student ADD Column '%s' text" % (lab + "URLSToGrade"))
				self.cursor.execute("Alter Table student ADD Column '%s' text" % (lab + "Grade"))
				
				
				#will add randomization stuff later...
				#self.cursor.execute("ALTER TABLE student ADD COLUMN '%s' text" % (lab + "RandomizedSpot"))	
				self.cursor.execute("ALTER TABLE expert ADD COLUMN '%s' text" % ("URL"))
				self.cursor.execute("Alter Table expert ADD Column '%s' text" % ("grade"))
				self.cursor.execute("ALTER TABLE expert ADD COLUMN '%s' int" % ("hidden")) 
			except:
				pass #
		self.conn.commit()

	#adds a person into the database, works for both new users and existing ones 
	def addEntry(self, wID, URL = None, labNumber = None, overwrite = False):
		if self.databaseName != None and self.conn != None and self.cursor !=None:
			self.cursor.execute("SELECT * FROM student WHERE wID = ?", [wID])
			#adds in a user if not in database already
			if self.cursor.fetchone() ==  None:
				self.cursor.execute("INSERT INTO student (wID) VALUES (?)", [wID])
				self.conn.commit()	
			
			params = ("Lab"+str(labNumber) + "URL", None)
			
			query = ("SELECT wID FROM student where {0}=?".format(*params))
			wIDswithDuplicateURLS = self.cursor.execute(query, [URL]).fetchall()
			
			if len(wIDswithDuplicateURLS) == 1 and URL !='':
				print str(wIDswithDuplicateURLS[0][0]) + " and " + wID + " submitted the same URL: " + URL
				URL = "DUPLICATEURL"		
			
			
			
			query = ("SELECT {0} FROM student WHERE wID=?".format(*params))
			prevInsertedLab =  self.cursor.execute(query, [wID]).fetchall()[0][0]
			if prevInsertedLab == None or overwrite == True:
			
				#inserts the URL for the specific lab into database
				query = ("UPDATE student SET {0}=? WHERE wID=?".format(*params))
				self.cursor.execute(query, (URL, wID))
				##perhaps write out to a logcat file to show that a value has been overwritten
				self.conn.commit()
			elif prevInsertedLab == URL:
				print("The URL "+str(URL)+" submitted by "+str(wID)+" is already present in the database")
			else:
				sys.exit("Trying to overrite the Youtube URL: " + prevInsertedLab + " from student with wID: " + wID)	

	#retrieves URL for a specific student and specific lab number
	def getURL(self, wID, labNumber):
		
		#finds all the columns, so the if loop below can see if the Lab#URL column exists
		self.cursor.execute("PRAGMA table_info(student)")
		data = self.cursor.fetchall()
		columnNames = [str(d[1]) for d in data]
		
		# ensures that the wID is in the database
		params = ("Lab" + str(labNumber) + "URL", None)
		self.cursor.execute("SELECT wID FROM student")
		wIDexists = wID in [str(id[0]) for id in self.cursor.fetchall()]
		if "Lab" + str(labNumber) + "URL" in columnNames and wIDexists:
			params = ("Lab" + str(labNumber) + "URL", None)
			query = ("SELECT {0} FROM student WHERE wID = ?".format(*params))
			self.cursor.execute(query, [wID])
			URL = self.cursor.fetchone()
			return URL[0]
		elif "Lab" + str(labNumber) + "URL" not in columnNames:
			sys.exit("Lab Number: " + str(labNumber) + " is not present in the database, add another lab number with the addLab() function")
		else:
			sys.exit("The wID: " + str(wID) + " is not in the database, use the addEntry() function to add the wID to the database")
	def addExpertURL(self, labNumber, URL,  grade, hidden):
		
		self.cursor.execute("SELECT * FROM expert WHERE URL = ?", [URL])
		#adds in a user if not in database already
		presentURL = self.cursor.fetchone()
		if presentURL ==  None:
			self.cursor.execute("INSERT INTO expert VALUES (?, ?, ?, ?)", [labNumber, URL, listToString(grade), hidden])
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
		self.cursor.execute("SElECT URL, grade FROM expert where labNumber=?", [labNumber])
		URLsAndGrades = {}
		for d in self.cursor.fetchall():
			URLsAndGrades[str(d[0])] = stringToList(str(d[1]))
		return URLsAndGrades

	def finalize(self, labNumber, seed, N, MOOC=False):
		##randomize the youtube URLs
		#for each wID
			#put that into the databse under the student ID
		self.cursor.execute("SELECT URL FROM expert WHERE labNumber=? and hidden=0", [labNumber])
		expertURL = [str(d[0]) for d in self.cursor.fetchall()]
		

		# find all the hidden expert videos	
		self.cursor.execute("SELECT URL FROM expert WHERE labNumber=? and hidden=1", [labNumber])
		hiddenURL = [str(d[0]) for d in self.cursor.fetchall()]
		
		#get all the studnet URLs
		params = ("Lab" + str(labNumber) + "URL", None)
		query = ("SELECT {0}  from student".format(*params))
		self.cursor.execute(query) 
		data = [str(d[0]) for d in self.cursor.fetchall()]
		
		
		#assign the students whos videos are designated expert graded URLs to grade, and remove them from the URL pool retrieved above
		if len(expertURL) + N + 1 <= len(data):
			pseudoURL = {}
			for d in expertURL:
				#if the expertURL is not in the data list, then it is a video that is not submitted by a student this sem
				#semester, in which case, we skip it
				if d in data:
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


		query = ("SELECT wID FROM student WHERE {0} is ''".format(*params))
		self.cursor.execute(query)
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


		query = ("SELECT wID FROM student WHERE {0}=?".format(*params))
		self.cursor.execute(query, ["DUPLICATEURL"])
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
			params = ("Lab" + str(labNumber) + "URLSToGrade", "Lab" + str(labNumber) + "URL")
			for key in pseudoURL.keys():
				startIndex = selectFrom.index(pseudoURL[key])
				URLSToGrade = selectFrom[startIndex: startIndex+N+1]
				query = ("UPDATE student SET {0}=? WHERE {1}=?".format(*params))
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				self.cursor.execute(query, [listToString(expertURL + URLSToGrade), key])
				self.conn.commit()
		if len(wIDPseudoURL.keys()) > 0:
			params = ("Lab" + str(labNumber) + "URLSToGrade", "Lab" + str(labNumber) + "URL")
			for key in wIDPseudoURL.keys():
				startIndex = selectFrom.index(wIDPseudoURL[key])
				URLSToGrade = selectFrom[startIndex: startIndex+N+1]
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				query = ("UPDATE student SET {0}=? WHERE wID=?".format(*params))
				self.cursor.execute(query, [listToString(expertURL + URLSToGrade), key])
				self.conn.commit()
			
		if len(data) > N:
			for d in data:
				startIndex = selectFrom.index(d)
				URLSToGrade = selectFrom[startIndex:startIndex+N+1]
				for i in hiddenURL: 
					URLSToGrade.append(i)
				random.shuffle(URLSToGrade)
				params = ("Lab" + str(labNumber) + "URLSToGrade", "Lab" + str(labNumber) + "URL")
				query = ("UPDATE student SET {0}=? WHERE {1} = ?".format(*params))
				self.cursor.execute(query, [listToString(expertURL + URLSToGrade), d])
		self.conn.commit()
		##this failed...try something else

		#if len(expertURL) + N + 1 <= len(data):
		#	URLSToDelete = expertURL + hiddenURL
		#	while len(expertURL) > 0:
		#		indice = data.index(expertURL[0])
		#		existsURLToDelete = True		
		#		while existsURLToDelete:
		#			URLsToGrade = data[indice:indice+N+1]
		#			for i in URLSToDelete:
		#				if URLsToGrade.count(i) > 0:
		#					indice = data.index(i)
		#			if data[indice] == 
				
		#selectFrom = data + data[:N + C + 1]
		#if len(data) > N + 1:
		#	for i in range(len(data)):
		#		URL = data[i]
		#		if hiddenURL != None:
		#			URLsToGrade = [hiddenURL] + selectFrom[i:i+N+1]
		#		#random.shuffle(URLsToGrade)
		#		params = ("Lab" + str(labNumber) + "URL", "Lab" + str(labNumber) + "URLsToGrade")
		#		query = ("UPDATE student SET {1}=? WHERE {0}=?".format(*params))
		#		self.cursor.execute(query, (listToString(URLsToGrade), URL))
		#		self.conn.commit()

	def getURLsToGrade(self, wID, labNumber):
		params = ("Lab" + str(labNumber) + "URLsToGrade", None)
		query = ("Select {0} FROM student WHERE wID=?".format(*params))
		self.cursor.execute(query, [wID])
		dbExtract = self.cursor.fetchone()
		if dbExtract == None:
			return False
		else:
			return [i for i in stringToList(dbExtract[0])]
	
	def addGrade(self, wID, labNumber, URL, grade, practice = False):
		params = ("Lab" + str(labNumber) + "URLSToGrade", "Lab" + str(labNumber))
		query = ("SELECT {0} FROM student where wID=?".format(*params))
		self.cursor.execute(query, [wID])
		URLsToGrade = self.getURLsToGrade(wID, labNumber)
		if URLsToGrade != False:
			if URL in URLsToGrade:
				query = ("INSERT INTO grades VALUES (?, ?, ?, ?, ?)".format(*params))
				self.cursor.execute(query, [labNumber, URL, wID, listToString(grade), practice])
				self.conn.commit()
			else:
				print "wID: " + wID + " was not assigned to grade URL: " + URL
		else:
			print("wID: " + wID + " not in the student table")

	def wIDGradesSubmitted(self, wID, labNumber, filename = None):
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
		params = ("Lab" + str(labNumber) + "URL", "Lab" + str(labNumber) + "URLsToGrade", None)
		query = ("Select {0}, {1} FROM student WHERE {0} != ''").format(*params)
		self.cursor.execute(query)
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
	sqldb.createTables(5)
	sqldb.addEntry("1", "1lkjsdf", 1)
	sqldb.addEntry("2", "1lkjsdf", 1)
	sqldb.addEntry("3", "1lkjsdf", 1)
	sqldb.addEntry("4", "4lkjsdf", 1)
	# sqldb.addEntry("4a",None , 2)
	sqldb.addEntry("4a",'' , 2)
	sqldb.addEntry("5", "5lkjsdf", 1)
	sqldb.addEntry("6", "6lkjsdf", 1)
	sqldb.addEntry("7", "7lkjsdf", 1)
	sqldb.addExpertURL(1, "5lkjsdf",[1, 2, 3, 4, 5, 6, 7], 0)
	sqldb.addExpertURL(1, "2lkjsdf", [1, 7, 3, 1, 6, 3], 0)
	# sqldb.addEntry("8", None, 2)
	sqldb.addEntry("8", '', 2)
	sqldb.addEntry(9, "hidden", 1)
	sqldb.addExpertURL(1, "hidden", [1, 2, 3], 1)
	print "testing below"
	sqldb.finalize(1, 1, 4)
	print sqldb.getURLsToGrade("1", 1)
	sqldb.addGrade("1",1,  "5lkjsdf", [1, 2, 3, 4])
	sqldb.addGrade("12",1,  "asdf", 1)
	sqldb.addGrade("1", 1, "2kjla", 1)
	sqldb.addGrade("2", "1", "5lkjsdf", [4, 3, 2, 1])
	sqldb.wIDGradesSubmitted("1", 1)
	sqldb.getGrades("5", 1)
	sqldb.getExpertURLs(1)
	sqldb.compareToExpert("1",1)
# sqldb.addExpert("expertVideo", 1, 1)		
# sqldb.addExpert("test2", 2, 2)

