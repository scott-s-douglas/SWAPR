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
from scipy.stats import sem

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
