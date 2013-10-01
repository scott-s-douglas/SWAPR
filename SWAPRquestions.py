from sqlite1 import *

def createQuestionsTable(db):
	db.cursor.execute("CREATE TABLE IF NOT EXISTS questions (labNumber int, questionNumber int, questionWebassignNumber int, practice boolean)")

def addAssignmentQuestion(db, labNumber, questionNumber, questionWebassignNumber, practice = False):
	db.cursor.execute("INSERT INTO questions VALUES (?, ?, ?, ?)",[labNumber, questionNumber, questionWebassignNumber, practice])
	db.conn.commit()

def addDefaultQuestions(db, labNumber):
	# The Webassign question numbers won't always be consecutive!
	questionNumbers = [2692884,2692888,2692889,2692890,2694521,2694522,2694523,2694524,2694525]
	for i in range(len(questionNumbers)):
		addAssignmentQuestion(db, labNumber, i+1, questionNumbers[i], practice = i <= 1)

def getQuestionIndexDict(db, labNumber):
    # Map the Webassign questions onto their corresponding indices in URLsToGrade
    db.cursor.execute("SELECT questionNumber, questionWebassignNumber FROM questions WHERE labNumber = ?", [labNumber])
    return { d[1]: d[0] for d in db.cursor.fetchall() }

def getQuestionPracticeDict(db, labNumber):
	# Map the Webassign questions onto booleans which say whether they're practice questions or not
	db.cursor.execute("SELECT questionWebassignNumber, practice FROM questions where labNumber = ?", [labNumber])
	return { d[0]: d[1] for d in db.cursor.fetchall() }