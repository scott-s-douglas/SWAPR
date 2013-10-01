from __future__ import division, print_function
from SWAPRv02_Lab11 import *
import pickle
from random import *
import numpy as np
import matplotlib.pyplot as plt
import math


# Set the random seed, for repeatability
# randomSeed = 474747436
randomSeed = 23094729837

# Student and expert files
studentsFiles = ['Lab11LinksM.txt','Lab11LinksHP.txt']

expertsFiles = ['Lab11Experts.txt']

gradesFiles = ['Lab11_Grades_M.txt','Lab11_Grades_HP.txt']

# Number of non-expert-graded videos to be graded by each student
ne = 5

# Number of expert-graded videos to be graded by each student
n = 3

# Number of items per rubric
R = 10

# Indices of Yes/No/Difficult to Say items
yndItems = [0,1]

# Indices of 5-point Likert-Scale items
likertItems = [2,4,6,8]

# Indices of not-to-be-graded items (including comment)
noGradeItems = [3,5,7,8,9]

# Index of comment item(s)
commentItem = [3,5,7,9]

preCorrectedStudents = ['pbodiwala6@gatech','aboyd33@gatech','mchickvary3@gatech','kflanagan9@gatech','jforeman9@gatech','sgrant8@gatech','ahsieh7@gatech','shughes33@gatech','mhuling3@gatech','yjia39@gatech','kjohnson308@gatech','kmays7@gatech','bmcgowan6@gatech','cmurphey3@gatech','anguyen45@gatech','eobrien9@gatech','spatel354@gatech','aprice37@gatech','bsavitske3@gatech','ssna6@gatech','atrujillo30@gatech','dward40@gatech','pweiland3@gatech','jwhitfield30@gatech','ywu342@gatech','ezhu7@gatech']

print('Reading students...')
students = studentList(studentsFiles)

# Manually read in the videos-to-grade
with open('Lab11GradingAssignmentsPRECORRECTION.txt','r') as assignmentsPRE:
    with open('Lab11GradingAssignmentsPOSTCORRECTION.txt','r') as assignmentsPOST:
        for line in assignmentsPOST:
            thisLine = line.split('\t')
            students.find(thisLine[1]).videosToGrade = thisLine[3:]
        for line in assignmentsPRE:
            thisLine = line.split('\t')
            if thisLine[1] in preCorrectedStudents:
                students.find(thisLine[1]).videosToGrade = thisLine[3:]
                # print('Reassigned videos to '+thisLine[1])


print('Reading experts...')
experts = expertList(expertsFiles)

# with open("Lab9Links.html",'w') as linkFile:
#     for student in students:
#         if student.hasValidLink():
#             linkFile.write('<a href='+student.link+'>'+student.fullName+'</a><br>\n')

# Assign the student videos
# assignVideos(students,experts,ne,n,R,randomSeed)

students.readGrades(gradesFiles, yndItems, likertItems, commentItem)

students.distributeGrades()




# students.writeWebassignOutput(questionFile='Lab11question.txt',answerFile='Lab11answer.txt')

# Print out overwhelmingly complete data dump
with open('Lab11DataDump.txt','w') as datadump:
    datadump.write('Student Name\tStudent ID\tStudent Video')
    for i in range(n+ne+1):
        datadump.write('\tGraded Video '+str(i+1))
        for j in range(R):
            datadump.write('\tRubric Item '+str(j+1))
    datadump.write('\n')
    for student in students:
        datadump.write(student.fullName+'\t'+student.webassignID+'\t'+student.video)
        for grade in student.gradesGiven:
            datadump.write('\t'+grade.videoID)
            for item in grade:
                datadump.write('\t'+str(item))
            for item in grade.comments:
                datadump.write('\t'+str(item))
        datadump.write('\n')

# alignments = []
# normDiffs = []

# for student in students:
#     if len(student.gradesGiven) == n + ne + 1:
#         student.calibrate(experts,noGradeItems)
#         alignments.append(student.calibration.alignment)
#         normDiffs.append(student.calibration.normDiff)
# for alignment in alignments:
#     if math.isnan(alignment):
#         alignments.pop(alignments.index(alignment))
# for normDiff in normDiffs:
#     if math.isnan(normDiff):
#         normDiffs.pop(normDiffs.index(normDiff))

# defaultWeight = 0.1

# Assign average grades
# for student in students:
#     if student.hasValidLink():
#         # for grade in student.gradesReceived:
#         #     j=0
#         #     for i in range(len(grade)):
#         #         if i not in noGradeItems:
#         #             student.finalGrade += grade[i]
#         #             j += 1
#         # student.finalGrade = student.finalGrade/(len(student.gradesReceived))
#         try:
#             student.finalGrade = 100*sum([ grade[i] for grade in student.gradesReceived for i in range(len(grade)) if i not in noGradeItems ])/(21*len(student.gradesReceived))
#         except:
#             print(student.fullName+' grade calculation failed.')
#     if student.gradesReceived not in [ [], None]:
#         for j in range(len(student.gradesReceived[0])):
#             thisNums = 0
#             weights = 0
#             for i in range(len(student.gradesReceived)):
#             # if j not in noGradeItems:
#                 thisNums += student.gradesReceived[i][j]
             
#             student.finalGradeVector.append(thisNums/len(student.gradesReceived))
# for student in students:
#     if student.hasValidLink():
#         weightedGrades = []
#         weights = []
#         # THIS IS SPECIFIC TO LAB 7
#         for grade in student.gradesReceived:
#             grader = students.find(grade.graderID)
#             if grader.calibrated:
#                 # print(student.video)
#                 weightedGrades.append(((sum(grade)-grade[5])*grader.calibration.weight)/21)
#                 # weightedGrades.append(np.mean(grade)/5)
#                 weights.append(grader.calibration.weight)
#         if sum(weightedGrades) > 0:
#             student.finalGrade = 100*(sum(weightedGrades)/sum(weights))

#         # Let's also get the calibrated grade vector, too
#         if student.gradesReceived not in [ [], None]:
#             for j in range(len(student.gradesReceived[0])):
#                 thisNums = 0
#                 weights = 0
#                 for i in range(len(student.gradesReceived)):
#                     grader = students.find(student.gradesReceived[i].graderID)
#                     try:
#                         weight = student.calibration.weight
#                     except AttributeError:
#                         weight = defaultWeight
#                     try:
#                         thisNums += student.gradesReceived[i][j]*weight
#                         weights += weight
#                     except:
#                         pass
                    
#                 student.finalGradeVector.append(thisNums/weights)

# # Write out the calibration values and weights
# with open('Lab9calibration.txt','w') as textfile:
#     textfile.write('Student ID'+'\t'+'Lab9 NormDiff'+'\t'+'Lab9 Alignment'+'\t'+'Lab9 Weight'+'\n')
#     for student in students:
#         textfile.write(student.webassignID+'\t')
#         try:
#             textfile.write(str(student.calibration.normDiff)+'\t'+str(student.calibration.alignment)+'\t'+str(student.calibration.weight)+'\n')
#         except:
#             textfile.write('\t\t\n')


            

# for student in students:
#     print(student.finalGrade)

# print('Mean student grade (excluding zeros): '+str(np.mean([student.finalGrade for student in students if student.finalGrade != 0])))
# print('Median student grade (excluding zeros): '+str(np.median([student.finalGrade for student in students if student.finalGrade != 0])))

# print('Writing full grade report...')


# with open('Lab11FullGradeReport.txt','w') as gradeFile:
#     for student in students:
#         gradeFile.write(student.fullName+'\t'+student.webassignID+'\t'+student.link+'\t'+str(student.finalGrade))
#         if len(student.finalGradeVector) > 0:
#             for num in student.finalGradeVector:
#                 gradeFile.write('\t'+str(num))
#         gradeFile.write('\n')

# print('Writing comments...')
# with open('Lab11CommentReport.txt','w') as commentFile:
#     for student in students:
#         commentFile.write(student.fullName+'\t'+student.webassignID)
#         for grade in student.gradesReceived:
#             try:
#                 for comment in grade.comments:
#                     commentFile.write('\t'+comment)
#             except:
#                 pass
#         commentFile.write('\n')


# # normCutoff = 3
# # alignmentCutoff = 0.92

# # # # print('Numer of "expert-like" students: '+str(len([student for student in students if student.calibrated and student.calibration.alignment > alignmentCutoff and abs(student.calibration.normDiff) < normCutoff])))

# # # # # Make a histogram of grades
# # # # studentGrades = [num for student in students for grade in student.gradesGiven for num in grade if grade.videoID == experts[1].videoID and student.calibrated and student.calibration.alignment > alignmentCutoff and abs(student.calibration.normDiff) < normCutoff]
# studentGrades = [student.finalGrade for student in students]
# # # # # # print(studentGrades)
# # # # # # expertGrades = [4,5,5,5,4,5,5,5,5,4,4,4,4,5,4,4,4,4,4,4,4,5,4,4]    # Good video
# # # # # # expertGrades = [3,2,3,4,5,4,3,4,3,2,1,1,3,2,2,2,3,2,2,1,1,2,1,1]    # Middling video
# # # # # # expertGrades = [3,3,3,3,2,3,3,2,2,3,3,1,2,3,2,1,2,1,2,2,1,1,1,1]    # Poor video
# fig, ax = plt.subplots()
# # # # # # ax.hist(studentGrades,bins=(0.5,1.5,2.5,3.5,4.5,5.5),normed=True,histtype='stepfilled')
# # # # # # ax.hist(expertGrades,bins=(0.5,1.5,2.5,3.5,4.5,5.5),normed=True,histtype='stepfilled',alpha=0.5)
# ax.hist(studentGrades,histtype='stepfilled',bins=50)
# # # # # ax.set_xticks([1,2,3,4,5])
# # # # # bbox_props = dict(boxstyle="rarrow,pad=0.3", fc="green", ec="w", lw=2)
# # # # # t = ax.text(np.mean(expertGrades), 0.05, "Expert Mean", ha="center", va="bottom", rotation=-90, size=15, color='w', bbox=bbox_props)
# # # # # bbox_props = dict(boxstyle="rarrow,pad=0.3", fc="blue", ec="w", lw=2,alpha=0.5)
# # # # # p = ax.text(np.mean(studentGrades), 0.05, "Student Mean", ha="center", va="bottom", rotation=-90, size=15, color='w', bbox=bbox_props)
# plt.title('Lab 11 Grades (Calibrated)')
# plt.xlabel('Grade')
# plt.ylabel('Number of Students')
# # # # # # # plt.xlim([0.5,5.5])
# # # # # # # plt.ylim([0,1])
# plt.show()

# SAVE ASSIGNMENT FOR FUTURE REFERENCE
# ====================================
# Pickle students and experts (such that you can load the objects into memory later)
# objectPickle = open('Lab11Objects.txt','wb')
# pickle.dump([students,experts],objectPickle)
# objectPickle.close()

# Write students and grading assignments to a human-readable tab-delimited .txt file
# assignmentFile = open('Lab11GradingAssignmentsPRECORRECTION.txt','w')
# assignmentFile.write('Random Seed = '+str(randomSeed)+'\tFilenames = '+str([studentsFiles,expertsFiles])+'\nFullname\tUsername\tSubmitted YouTubeID\tAssigned YouTubeID\n')
# for student in students:
#     assignmentFile.write(student.fullName+"\t"+student.webassignID+"\t")
#     if student.hasValidLink():
#         assignmentFile.write(student.video)
#     else:
#         assignmentFile.write('(No Video)')


#     for link in student.videosToGrade:
#         assignmentFile.write("\t"+getYoutubeID(link))
#     assignmentFile.write("\n")
# assignmentFile.close()





