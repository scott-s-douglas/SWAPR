from sqlite1 import *

def createRubricsTable(db):
    db.cursor.execute("CREATE TABLE IF NOT EXISTS rubrics (labNumber int, itemIndex int, itemType text, itemValues text, graded boolean, itemPrompt text)")

def addRubricItem(db, labNumber, itemIndex, itemType, itemValues, graded, itemPrompt = None):
    db.cursor.execute("INSERT INTO rubrics VALUES (?, ?, ?, ?, ?, ?)", [labNumber, itemIndex, itemType, listToString(itemValues), graded, itemPrompt])
    db.conn.commit()

def getRubricGradedDict(db,labNumber):
    db.cursor.execute("SELECT itemIndex, graded FROM rubrics WHERE labNumber = ?", [labNumber])
    return { d[0]: d[1] for d in db.cursor.fetchall() }

def getRubricTypeDict(db,labNumber):
    db.cursor.execute("SELECT itemIndex, itemType FROM rubrics WHERE labNumber = ?", [labNumber])
    return { d[0]: d[1] for d in db.cursor.fetchall() }

def getRubricValuesDict(db,labNumber):
    # Returns a list of dictionaries; each item index yields a dictionary of item responses (on Webassign, 0,1,2,etc.) vs. point values (12,10,6,4,etc.)
    db.cursor.execute("SELECT itemIndex, itemType, itemValues FROM rubrics WHERE labNumber = ? AND graded", [labNumber])
    valuesDict = []
    for d in db.cursor.fetchall():
        if d[1] == 'likert5':
            itemValuesDict = { [4,3,2,1,0][i]: [float(entry) for entry in stringToList(d[2])][i] for i in range(len(stringToList(d[2]))) }
        elif d[1] in ['yhn','likert3']:
            itemValuesDict = { [2,1,0][i]: [float(entry) for entry in stringToList(d[2])][i] for i in range(len(stringToList(d[2]))) }
        valuesDict.append(itemValuesDict)
    return valuesDict

def getMaxScore(db,labNumber):
    scores = getRubricValuesDict(db,labNumber)
    maxScore = 0
    for item in scores:
        maxScore += max(item.values())

    return maxScore


def addDefaultRubric(db, labNumber):
    # Make sure the Wnumbers are actually consecutive on WebAssign!
    addRubricItem(db, labNumber, 1, 'likert5', [0,2,6,10,12], True, 'The video presentation is clean and easy to follow.')
    addRubricItem(db, labNumber, 2, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the video presentation?')
    addRubricItem(db, labNumber, 3, 'yhn', [0,6,12], True, 'Does the video introduce the problem and state the main result?')
    addRubricItem(db, labNumber, 4, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the introduction and the statements of the main result?')
    addRubricItem(db, labNumber, 5, 'yhn', [0,6,12], True, 'Does the video identify the model(s) relevant to this physical system?')
    addRubricItem(db, labNumber, 6, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the discussion of how the main physics ideas are applied in the problem under study?')
    addRubricItem(db, labNumber, 7, 'likert5', [0,0.5,1,1.5,2], True, 'The computational model(s) successfully predict(s) the motion of the object observed.')
    addRubricItem(db, labNumber, 8, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve how well his/her computational model(s) predicted the motion of the object?')
    addRubricItem(db, labNumber, 9, 'likert5', [0,2,6,10,12], True, 'The presenter successfully discusses how his/her computational model(s) predicts or fails to predict the motion of the object.')
    addRubricItem(db, labNumber, 10, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve his/her EXPLANATION of how his/her model predicted the motion of the object?')
    addRubricItem(db, labNumber, 11, 'likert5', [0,2,6,10,12], True, 'The video presentation correctly explains the physics.')
    addRubricItem(db, labNumber, 12, 'freeResponse', [], False, 'Were there any aspects of the physics in this video which the presenter did not make clear? Was the presenter mistaken about some of the physics he or she presented?')
    addRubricItem(db, labNumber, 13, 'comparative5', [-2,-1,0,1,2], False, 'How does this video compare to your own video?')
    addRubricItem(db, labNumber, 14, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve his/her report, or what are a couple of things you have learned from this video to improve your own report?')

