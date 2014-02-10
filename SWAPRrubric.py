from SWAPRsqlite import *
from itertools import groupby

def createRubricsTable(db):
    db.cursor.execute("CREATE TABLE IF NOT EXISTS rubrics (labNumber int, itemIndex int, itemType text, itemValues text, graded boolean, itemPrompt text)")

def addRubricItem(db, labNumber, itemIndex, itemType, itemValues, graded, itemPrompt = None):
    db.cursor.execute("INSERT INTO rubrics VALUES (NULL, ?, ?, ?, ?, ?)", [labNumber, itemIndex, itemType, itemPrompt, graded])
    if itemValues == []:
        db.cursor.execute("INSERT INTO responseKeys VALUES (NULL,?,?,?,?)",[labNumber,itemIndex,0,None])
    for i in range(len(itemValues)):
        db.cursor.execute("INSERT INTO responseKeys VALUES (NULL, ?,?,?,?)",[labNumber, itemIndex,i,float(itemValues[-(i+1)])])
    db.conn.commit()

def getMaxScore(db,labNumber):
    # assumes max score corresponds with response 0
    db.cursor.execute("SELECT score FROM responseKeys, rubrics WHERE response = 0 AND responseKeys.labNumber = ? AND responseKeys.itemIndex = rubrics.itemIndex AND responseKeys.labNumber = rubrics.labNumber AND graded",[labNumber])
    maxScoreVector = [float(entry[0]) for entry in db.cursor.fetchall()]
    maxScore = sum(maxScoreVector)

    return maxScore, maxScoreVector

def getNgradedItems(db,labNumber,likert5only=False):
    "Return the number of graded items in a particular lab's rubric. This function makes a SQLite call, so don't run it between a select and a fetch on that same database."
    if not likert5only:
        db.cursor.execute('''SELECT count(*)
            FROM rubrics
            WHERE
                labNumber = ?
                AND graded
            ''',[labNumber])
    else:
        db.cursor.execute('''SELECT count(*)
            FROM rubrics
            WHERE
                labNumber = ?
                AND graded
                AND itemType = 'likert5'
            ''',[labNumber])
    Ngraded = int(db.cursor.fetchone()[0])
    return Ngraded

def getScoresDict(db,labNumber):
    # Construct a dictionary of dictionaries where each possible response is paired with its score for GRADED items only
    db.cursor.execute('''SELECT k.itemIndex, k.response, k.score 
        FROM responseKeys k, rubrics r 
        WHERE 
            --match labNumber
            r.labNumber = ?
            AND r.labNumber = k.labNumber 
            --match itemIndex
            AND r.itemIndex = k.itemIndex
            AND k.score IS NOT NULL 
            AND r.graded
        ORDER BY k.itemIndex, k.response, k.score''',[labNumber])
    data = [[int(entry[0]),int(entry[1]),float(entry[2])] for entry in db.cursor.fetchall()]
    scoresDict = {}
    for itemIndex, itemIndexGroup in groupby(data, lambda entry: entry[0]):
        thisScores = {}
        for pair in itemIndexGroup:
            thisScores.update({pair[1]:pair[2]})
        scoresDict.update({itemIndex:thisScores})
    return scoresDict


def addDefaultRubric(db, labNumber):
    # Make sure the Wnumbers are actually consecutive on WebAssign!
    if labNumber == 3:
        addRubricItem(db, labNumber, 1, 'likert5', [0,2,6,10,12], True, 'The video presentation is clean and easy to follow.')
        addRubricItem(db, labNumber, 2, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the video presentation?')
        addRubricItem(db, labNumber, 3, 'yhn', [0,6,12], True, 'Does the video introduce the problem and state the main result?')
        addRubricItem(db, labNumber, 4, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the introduction and the statements of the main result?')
        addRubricItem(db, labNumber, 5, 'yhn', [0,6,12], True, 'Does the video identify the model(s) relevant to this physical system?')
        addRubricItem(db, labNumber, 6, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the discussion of how the main physics ideas are applied in the problem under study?')
        addRubricItem(db, labNumber, 7, 'yhn', [0,1,2], True, 'The computational model(s) successfully predict(s) the mass of the black hole.')
        addRubricItem(db, labNumber, 8, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve how well his/her computational model(s) predicted the mass of the black hole?')
        addRubricItem(db, labNumber, 9, 'likert5', [0,2,6,10,12], True, 'The presenter successfully discusses how his/her computational model(s) predicts or fails to predict the mass of the black hole.')
        addRubricItem(db, labNumber, 10, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve his/her EXPLANATION of how his/her model predicted the mass of the black hole?')
        addRubricItem(db, labNumber, 11, 'likert5', [0,2,6,10,12], True, 'The video presentation correctly explains the physics.')
        addRubricItem(db, labNumber, 12, 'freeResponse', [], False, 'Were there any aspects of the physics in this video which the presenter did not make clear? Was the presenter mistaken about some of the physics he or she presented?')
        addRubricItem(db, labNumber, 13, 'comparative5', [-2,-1,0,1,2], False, 'How does this video compare to your own video?')
        addRubricItem(db, labNumber, 14, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve his/her report, or what are a couple of things you have learned from this video to improve your own report?')
    if labNumber == 6:
        addRubricItem(db, labNumber, 1, 'likert5', [0,2,6,10,12], True, 'The video presentation is clear and easy to follow.')
        addRubricItem(db, labNumber, 2, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the video presentation?')

        addRubricItem(db, labNumber, 3, 'yhn', [0,6,12], True, 'Does the presenter identify the lecture they attended and introduce the topic of that lecture?')
        addRubricItem(db, labNumber, 4, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the introduction and the problem statement? ')

        addRubricItem(db, labNumber, 5, 'yhn', [0,1,2], True, 'Does the presenter summarize the main points of the lecture and state why this topic was of interest to him or her?')
        addRubricItem(db, labNumber, 6, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the summary of the main points of the lecture? ')

        addRubricItem(db, labNumber, 7, 'likert5', [0,2,6,10,12], True, 'TThe presenter taught the viewer something interesting they learned as a result of attending this lecture.')
        addRubricItem(db, labNumber, 8, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve the summary of the main points of the lecture? ')

        addRubricItem(db, labNumber, 9, 'likert5', [0,2,6,10,12], True, 'The presenter followed up on the lecture with ideas or concepts not discussed by the public speaker.')
        addRubricItem(db, labNumber, 10, 'freeResponse', [], False, 'Were there any aspects of the physics in this video which the presenter did not make clear? Was the presenter mistaken about some of the physics he or she presented? ')

        addRubricItem(db, labNumber, 11, 'comparative5', [-2,-1,0,1,2], False, 'How does this video compare to your own video?')
        addRubricItem(db, labNumber, 12, 'freeResponse', [], False, 'What are a couple of things this presenter could do to improve his/her report, or what are a couple of things you have learned from this video to improve your own report?')
    else:
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


