from __future__ import division, print_function
from sqlite1 import *
from SWAPRstrings import *
from SWAPRweights import *
from SWAPRrubric import *
from SWAPRquestions import *
from SWAPRgrades import *
import csv
import re
import glob
from os import remove
from copy import copy
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.stats import sem

generateDB = True

randomSeed = 14539452394857692387452    # Used for Lab 1
# randomSeed = 239092750250    # Used for Lab 2

# .csv parameters
studentStartRow = 9     # First row of student data (everything in this script is 0-indexed)
expertStartRow = 0      # First row of expert data
studentLinkCol = 4      # Column containing YouTube URLs
expertLinkCol = 2       # Column containing YouTube URLs
studentFullNameCol = 0  # Column containing student's full name
wIDcol = 1  # Column with student's unique WebAssign ID ($STUDENT in WebAssign Perl)
gradeCol = 3            # Column which starts the expert grades
studentGradeCol = 4    # Column which starts the student grades

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
    db.cursor.execute("SELECT wID FROM student")
    wIDs = db.cursor.fetchall()
    for wID in wIDs:
        URLs = getURLsToGradeLab1Debug(str(wID[0]),fixFilename)
        db.cursor.execute("UPDATE student SET Lab1URLSToGrade=? WHERE wID=?", (listToString(URLs), str(wID[0])))
    db.conn.commit()

if False:
    print("Generating campus Lab 2 assignment...")
    try:
        os.remove("campus2.db")
    except:
        pass
    makeDatabase("campus2.db")
    campus2db = SqliteDB("campus2.db")
    campus2db.createTables(5)
    # pydbCampus = []

    # Parse all the files in the campus folder
    print("Parsing links files...")
    for file in listdir_nohidden('Lab 2 Campus Links/'):
        parseLinksFile(file,campus2db,2)
            # pydbCampus.append(entry)
    # Parse the experts file
    print("Parsing experts file...")
    parseExpertsFile('Lab2Experts.txt',campus2db,2)
        # pydbCampus.append(entry)

    print("Finalizing database...")
    campus2db.finalize(2, randomSeed, 3)

    print("Exporting WebAssign code...")
    exportWebassign('campus2.txt',campus2db,2)

if False:
    print("Generating public Lab 2 assignment...")
    try:
        os.remove("public2.db")
    except:
        pass
    makeDatabase("public2.db")
    public2db = SqliteDB("public2.db")
    public2db.createTables(5)
    # pydbPublic = []

    # Parse all the files in the public folder
    for file in listdir_nohidden('Lab 2 Public Links/'):
        parseLinksFile(file,public2db,2,skipLinkless=True)
            # pydbPublic.append(entry)
    # Parse the experts file
    parseExpertsFile('Lab2Experts.txt',public2db,2)
        # pydbPublic.append(entry)
    public2db.finalize(2,randomSeed,3)
    exportWebassign('public2.txt',public2db,2)

if True:
    #======================================
    # Generate the campus Webassign output
    if False:
        print("Generating campus assignment...")
        try:
            os.remove("campus.db")
        except:
            pass
        makeDatabase("campus.db")
        campusdb = SqliteDB("campus.db")
        campusdb.createTables(5)
        # pydbCampus = []

        # Parse all the files in the campus folder
        print("Parsing links files...")
        for file in listdir_nohidden('Lab 1 Campus/'):
            parseLinksFile(file,campusdb,1)
                # pydbCampus.append(entry)
        # Parse the experts file
        print("Parsing experts file...")
        parseExpertsFile('Lab1Experts.txt',campusdb,1)
            # pydbCampus.append(entry)

        print("Finalizing database...")
        campusdb.finalize(1, randomSeed, 3)

        print("Applying Lab 1 fix...")
        lab1URLfix(campusdb,"campusBackup.txt")

        # print("Checking database...")
        # if (campusdb.check(1)):
        #     print("All students who submitted a URL will receive their own URL to grade.")

        exportWebassign('campus.txt',campusdb,1)


        # publicwIDs = set([entry[0] for entry in pydbPublic])
        # exportWebassign('public.txt',publicdb,publicwIDs,1)
        #======================================
        # Consistency check

        createWeightsTableBIBI(campusdb)

        createRubricsTable(campusdb)
        addDefaultRubric(campusdb, 1)

        createQuestionsTable(campusdb)
        addDefaultQuestions(campusdb, 1)

        # Get the maximum score of one rubric
        maxScore = getMaxScore(campusdb,1)
        # print('Maxscore = '+str(maxScore))

        print("Parsing grades files...")
        for file in listdir_nohidden('Lab 1 Grades Campus/'):
            parseGradesFile(file,campusdb,1)

        print("Assigning weights...")
        assignWeightsBIBI(campusdb, 1, weightBIBI)

        print("Assigning final grades...")
        createFinalGradesTable(campusdb)
        assignGrades(campusdb,1,calibrated = True)


        # campusdb.cursor.execute("SELECT student.wID, finalGrade FROM student, finalGrades WHERE student.lab1URL = finalGrades.URL AND student.Lab1URL IS NOT NULL AND finalGrade = 0")
        # print([item[0] for item in campusdb.cursor.fetchall()])

        # campusdb.cursor.execute("SELECT student.wID FROM student, finalGrades WHERE finalGrades.wID = student.wID AND finalGrade = 0")
        # print("The following students got a 0 on their peer grade:")
        # for item in campusdb.cursor.fetchall():
        #     print(str(item[0]))


        # campusdb = SqliteDB("campus.db")
        printGradesReport(campusdb,'Lab1GTgrades.txt',1)
    #======================================
    # Generate the public Webassign output
if False:
    print("Generating public Lab 1 grades...")
    try:
        os.remove("public.db")
    except:
        pass
    makeDatabase("public.db")
    publicdb = SqliteDB("public.db")
    publicdb.createTables(5)
    # pydbPublic = []

    # Parse all the files in the public folder
    for file in listdir_nohidden('Lab 1 Public/'):
        parseLinksFile(file,publicdb,1,skipLinkless=True)
            # pydbPublic.append(entry)
    # Parse the experts file
    parseExpertsFile('Lab1Experts.txt',publicdb,1)
        # pydbPublic.append(entry)

    publicdb.finalize(1, randomSeed, 3)
    lab1URLfix(publicdb,"campusBackup.txt")

    createWeightsTableBIBI(publicdb)

    createRubricsTable(publicdb)
    addDefaultRubric(publicdb, 1)

    createQuestionsTable(publicdb)
    addDefaultQuestions(publicdb, 1)

    # Get the maximum score of one rubric
    maxScore = getMaxScore(publicdb,1)
    # print('Maxscore = '+str(maxScore))
    print("Parsing grades files...")
    for file in listdir_nohidden('Lab 1 Public Responses/'):
        parseGradesFile(file,publicdb,1)

    print("Assigning weights...")
    assignWeightsBIBI(publicdb, 1, weightBIBI)

    print("Assigning final grades...")
    createFinalGradesTable(publicdb)
    assignGrades(publicdb,1,calibrated = True)

    printGradesReport(publicdb,'Lab1MOOCgrades.txt',1)

# publicdb = SqliteDB("public.db")
# publicdb.cursor.execute("SELECT student.wID, student.lab1URL FROM student, finalGrades WHERE student.Lab1URL != '' AND finalGrade = 0 AND student.wID = finalGrades.wID")
# print([[str(student[0]),str(student[1])] for student in publicdb.cursor.fetchall()])

if False:
    campusdb.cursor.execute("SELECT weight1, weight2, weight3, weight4, weight5, weight6 FROM weightsBIBI WHERE labNumber = 1")
    weights = [sum([float(item) for item in d[1:-1]]) for d in campusdb.cursor.fetchall()]


    # finalFinalGrades = [0.25*weight + 0.5*finalGrade for weight, finalGrade in []]

    print("Plotting weights...")
    campusdb.cursor.execute('SELECT finalGrade FROM finalGrades WHERE labNumber = 1')
    data = campusdb.cursor.fetchall()

    finalGrades = [round(d[0]) for d in data]
    # print("Weights: "+str(len(weights))+" Grades: "+str(len(finalGrades)))
    # print(finalGrades)

    campusdb.cursor.execute('SELECT finalGrade, weight1, weight2, weight3, weight4, weight5, weight6, Lab1URL FROM finalGrades, weightsBIBI, student WHERE finalGrades.URL = student.Lab1URL AND weightsBIBI.wID = student.wID')
    # finalFinalGrades = [50*float(d[0])/(.75*maxScore) + 25*sum([float(item) for item in d[1:-1]])/(6*.75) for d in campusdb.cursor.fetchall()]
    finalFinalGrades = [50*float(d[0])/(maxScore) + 25*sum([float(item) for item in d[1:-1]])/(6) + 25 for d in campusdb.cursor.fetchall()]

    BIBIweights = []
    for i in range(6):
        campusdb.cursor.execute('SELECT weight'+str(i+1)+' FROM weightsBIBI')
        BIBIweights.append([float(item[0]) for item in campusdb.cursor.fetchall()])
    
if False:
    fig, ax = plt.subplots()

    i = 5
    # print(BIBIweights[i])
    ax.hist(finalGrades,histtype='stepfilled',bins=40)
    # ax.set_xticks([1,2,3,4,5])
    # # # # # bbox_props = dict(boxstyle="rarrow,pad=0.3", fc="green", ec="w", lw=2)
    # # # # # t = ax.text(np.mean(expertGrades), 0.05, "Expert Mean", ha="center", va="bottom", rotation=-90, size=15, color='w', bbox=bbox_props)
    # # # # # bbox_props = dict(boxstyle="rarrow,pad=0.3", fc="blue", ec="w", lw=2,alpha=0.5)
    # # # # # p = ax.text(np.mean(studentGrades), 0.05, "Student Mean", ha="center", va="bottom", rotation=-90, size=15, color='w', bbox=bbox_props)
    plt.title('Lab 1 Item '+str(i+1)+' Weights')
    plt.xlabel('Grade')
    plt.ylabel('Number of Students')
    plt.xlim([0,62])
    # ax.set_xticks([i/3 for i in range(6*3)])
    # ax.set_xticks([0,0.333,0.666,1])
    plt.ylim([0,20])
    plt.show()
