from __future__ import division, print_function
from sqlite1 import *
from SWAPRwebassignParser import *
from SWAPRstrings import *
from SWAPRweights import *
from SWAPRrubric import *
from SWAPRquestions import *
from SWAPRgrades import *
from SWAPRcomments import *
from SWAPRoutputWebassign import *
import csv
import re
import glob
from os import remove
from copy import copy
import numpy as np
import matplotlib.pyplot as plt
import math
# from scipy.stats import sem

def listdir_nohidden(path):
    # Return only the non-hidden files in a directory, to avoid that annoying .DS_Store file
    return glob.glob(os.path.join(path, '*'))

def getURLsToGradeLab1Debug(wID, fixFilename):
    # The data model changed between assignment of lab1 evaluation and the grading of lab1 evaluation, and I can't re-create exactly the same list of URLsToGrade, so I'm just going to hack it for the first lab.
    # We take all 4 expert URLs from Lab1Experts.txt, append to them the 5 videos we assigned them before (stored in campusBackup.txt and publicBackup.txt), and return those 9 in that order as URLsToGrade.
    URLs = []

    # Add the 4 common expert URLs
    with open('Lab1Experts.txt','rU') as text:
        for line in text:
            splitLine = line.split('\t') 
            if splitLine[-1] != '1\n':
                for entry in splitLine:
                    if getYoutubeLink(entry) is not '':
                        URLs.append(getYoutubeLink(entry))

    # Read in the 5 evaluation URLs (one of which is the hidden expert, one of which is the student's own)
    with open(fixFilename,'rU') as text:
        for line in text:
            if perlPerson(wID) in line:
                # print("Found "+wID+" in "+fixFilename)
                for entry in line.split('"'):
                    if getYoutubeLink(entry) is not '' and perlPerson(wID) not in entry:
                        URLs.append(getYoutubeLink(entry))
                break
        return URLs

def lab1URLfix(db, fixFilename):
    db.cursor.execute("SELECT wID FROM submissions")
    wIDs = db.cursor.fetchall()
    for wID in wIDs:
        URLs = getURLsToGradeLab1Debug(str(wID[0]),fixFilename)
        db.cursor.execute("UPDATE submissions SET Lab1URLSToGrade=? WHERE wID=?", (listToString(URLs), str(wID[0])))
    db.conn.commit()

if False:

    print("Generating campus assignment...")
    try:
        os.remove("testReconcile.db")
    except:
        pass
    makeDatabase("testReconcile.db")
    campusdb = SqliteDB("testReconcile.db")
    campusdb.createTables()

    # Parse all the files in the campus folder
    print("Parsing links files...")
    for file in listdir_nohidden('Lab 1 Campus/'):
        parseLinksFile(file,campusdb,1)
    # Parse the experts file
    print("Parsing experts file...")
    parseExpertsFile('Lab1Experts.txt',campusdb,1)
        # pydbCampus.append(entry)

    print("Finalizing database...")
    campusdb.finalize(1, randomSeed, 3)

    # print("Applying Lab 1 fix...")
    # lab1URLfix(campusdb,"testReconcile.txt")

    print("Exporting WebAssign question...")
    exportWebassign('testReconcile.txt',campusdb,1)

    print("Initializing weights table...")
    createWeightsTableBIBI(campusdb)

    print("Adding rubric...")
    createRubricsTable(campusdb)
    addDefaultRubric(campusdb, 1)

    print("Adding question table...")
    createQuestionsTable(campusdb)
    addDefaultQuestions(campusdb, 1)

    # Get the maximum score of one rubric
    maxScore = getMaxScore(campusdb,1)

    print("Parsing responses files...")
    for file in listdir_nohidden('Lab 1 Grades Campus/'):
        parseResponsesFile(file,campusdb,1)

    print("Assigning weights...")
    assignWeightsBIBI(campusdb, 1, weightBIBI)

    print("Assigning final grades...")
    createFinalGradesTable(campusdb)
    assignGrades(campusdb,1,calibrated = True)

if True:
    db = SqliteDB("2211 Fall 2013 Public.db")
    # db.cursor.execute("DROP TABLE students")
    # db.cursor.execute("DROP TABLE rubrics")
    # db.cursor.execute("DROP TABLE grades")
    # db.conn.commit()
    # db.createTables()

    # Parse all the files in the campus folder
    # db.cursor.execute("DELETE FROM submissions WHERE labNumber = 3")
    # db.conn.commit()
    # # db.cursor.execute("DELETE FROM experts WHERE labNumber = 4")
    # # print("Parsing links files...")
    # for file in listdir_nohidden('Lab 3 Public Links/'):
    #     parseLinksFile(file,db,3,skipLinkless = True)

    # db.cursor.execute("SELECT * FROM submissions WHERE labNumber = 3 AND wID LIKE '%hs_pugh%'")
    # print(db.cursor.fetchall())
    # # Parse the experts file
    # print("Parsing experts files...")

    # parseExpertsFile('Lab4Experts.txt',db,4)
    # # parseExpertsFile('Lab2Experts.txt',db,2)
    # # parseExpertsFile('Lab3Experts.txt',db,3)
    #     # pydbCampus.append(entry)
    randomSeed = 248273400029
    print("Finalizing database...")
    db.finalize(3, randomSeed, 3)

    # print("Applying Lab 1 fix...")
    # lab1URLfix(campusdb,"testReconcile.txt")

    # print("Exporting WebAssign question...")
    # exportWebassign('Lab 4 Campus Webassign.txt',db,4)

    # print("Initializing weights table...")
    # createWeightsTableBIBI(db)

    # print("Adding rubric...")
    # createRubricsTable(campusdb)
    # addDefaultRubric(db, 1)
    # addDefaultRubric(db, 2)
    # db.cursor.execute("DELETE FROM rubrics WHERE labNumber = 3")
    # db.conn.commit()
    # addDefaultRubric(db, 3)
    # addDefaultRubric(db, 4)

    # print("Adding questions...")
    # createQuestionsTable(campusdb)
    # addDefaultQuestions(db, 1)
    # addQuestions(db,2,[2708950,2709105,2709107,2709108,2708898,2708899,2708900,2708901,2708902])
    # addQuestions(db,3,[2727517,2727519,2727522,2727525,2734844,2734880,2734881,2734882,2734883])

    # Get the maximum score of one rubric
    # maxScore = getMaxScore(db,3)
    # db.cursor.execute('DROP TABLE grade')

    db.cursor.execute("DELETE FROM responses WHERE labNumber = 3")
    db.conn.commit()
    print("Parsing responses files...")
    for file in listdir_nohidden('Lab 3 Public Responses/'):
        print("Parsing "+str(file)+'...')
        parseResponsesFile(file,db,3)

    print("Assigning weights...")
    # assignWeightsBIBI(db, 1, weightBIBI)
    # assignWeightsBIBI(db, 2, weightBIBI)
    db.cursor.execute("DELETE FROM weightsBIBI WHERE labNumber = 3")
    db.conn.commit()
    assignWeightsBIBI(db, 3, weightBIBI)

    print("Assigning final grades...")
    db.cursor.execute("DELETE FROM grades WHERE labNumber = 3")
    # createFinalGradesTable(db)
    # assignGrades(db,1,calibrated = True)
    # assignGrades(db,2,calibrated = True)
    # db.cursor.execute("DELETE FROM grades WHERE labNumber = 3")
    assignGrades(db,3,calibrated = True)
    # parseEmails(db,'WebAssign Emails.csv')

    print('======================DONE======================')
# db = SqliteDB("2211 Fall 2013 Public.db")
printGradesReport(db,'Lab 3 Public Grades.txt',3)
# writeCommentsTabDelimited(db,'Lab 3 Public Comments.txt',3,writeEmails = True)