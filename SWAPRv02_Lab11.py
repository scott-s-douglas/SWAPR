from __future__ import division, print_function
import csv
import re
from random import shuffle, seed
from copy import copy
import numpy as np

# .csv parameters
studentStartRow = 9     # First row of student data (everything in this script is 0-indexed)
expertStartRow = 0      # First row of expert data
studentLinkCol = 5      # Column containing YouTube URLs
expertLinkCol = 2       # Column containing YouTube URLs
studentFullNameCol = 0  # Column containing student's full name
studentUserNameCol = 1  # Column with student's unique username ($STUDENT in WebAssign Perl)
expertFullNameCol = studentFullNameCol
expertUserNameCol = studentUserNameCol
gradeCol = 3            # Column which starts the expert grades
studentGradeCol = 4    # Column which starts the student grades


def getYoutubeID(string):
    # Get the YouTube ID from a URL or other string
    if string is not '' and string is not None:
        ID = re.search('[a-zA-Z0-9_-]{11}', string)
        if ID is not None:
            return ID.group(0)
    return ''

def getYoutubeLink(string):
    # Turn any string which contains a valid YouTube ID into a youtu.be link
    if string is not '' and string is not None:
        return 'http://youtu.be/'+getYoutubeID(string)
    return ''

def assignVideos(students, experts, ne=0, n=1, R=1, randomSeed=None):
    # Draw from the set of all student videos except the expert-graded ones AND the set of expert-graded videos; put the video assignments into student.videosToGrade

    students.R = R

    # Set the random seed, for repeatability
    if randomSeed is not None:
        seed(randomSeed)
    # Number of videos to be graded by each student, counting their own
    N = ne + n + 1
    # not counting their own
    # N = ne + n 

    # Total number of expert-graded videos
    if experts != None:
        E = len(experts.videos)
        expertVideos = experts.videos
    else:
        E = 0
        expertVideos = []

    # Number of students
    S = len(students)

    # Number of videos (==X if every student submitted a video)
    V = len(students.videos)

    # Assign links-to-grade to students

    nonExpertVideos = []
    for video in students.videos:

        # Create a list of all links which have not been graded by experts
        if video not in expertVideos:
            nonExpertVideos.append(video)
        # else:
            # print('Removed an expert link.')

    print('Assigning expert videos...')

    # EXPERT ASSIGNMENT
    # =================
    # Assign every student who submitted a link n expert links: this WILL FAIL iff n > E. We draw from the list of expert links in its original order, skipping over any entry which would assign a student their own link or a duplicate link. We also start each new column by setting j=i, but this is strictly redundant.
    if experts != None:
        j = 0
        k = 0
        for i in range(n):
            # j = i
            for student in students:
                while True:
                    thisVideo = expertVideos[j%E]
                    if thisVideo not in student.videosToGrade and thisVideo != student.video:
                        student.videosToGrade.append(thisVideo)
                        j += 1
                        break
                    elif thisVideo == student.video and len(expertVideos) == n:
                        # Special case where a student's own video has been expert-graded, and each student should be assigned all expert-graded links; we need to give the student another non-expert-graded link
                        k = 0
                        while True:
                            if nonExpertVideos[k%len(nonExpertVideos)] not in student.videosToGrade and nonExpertVideos[k%len(nonExpertVideos)] != student.video:
                                student.videosToGrade.append(nonExpertVideos[k%len(nonExpertVideos)])
                                break
                            k += 1
                        break

                    j += 1

    # NON-EXPERT ASSIGNMENT
    # =====================
    # Assign every student N-n non-expert links. We draw from a shuffled list of the non-expert links, skipping entries which would assign a student their own link or a duplicate link. We also start each new column by setting j=i, but this is redundant and probably undesirable.
    shuffle(nonExpertVideos)

    # Sanity check: make sure we have the right number of non-expert links
    if len(nonExpertVideos) != V-E:
        print('Warning: Improper number of non-expert links: '+str(len(nonExpertVideos))+', should be '+str(V-E))
    print('Students='+str(S)+', Videos='+str(V)+', Expert-graded videos='+str(E))

    j = 0
    k = 0
    for student in students:
        for i in range(ne + 1 - int(student.hasValidLink())): # Students without their own videos get one extra non-expert video
            j = k
            while True:
                thisVideo = nonExpertVideos[j%len(nonExpertVideos)]
                if thisVideo not in student.videosToGrade and thisVideo != student.video:
                    student.videosToGrade.append(thisVideo)
                    j += 1
                    break
                j += 1
        k += 1

    # SELF-ASSIGNMENT
    # ===============
    # Finally, assign every student their own video if they have one.
    for student in students:
        if student.hasValidLink():
            if student.video not in student.videosToGrade:
                student.videosToGrade.append(student.video)


    # Shuffle each student's videos-to-grade to eliminate ordering bias
    for student in students:
        shuffle(student.videosToGrade)

    # Sanity check: make sure we didn't assign any duplicate videos
    i = 0
    for student in students:
        if len(student.videosToGrade) != len(set(student.videosToGrade)):
            i += 1
            print(student)
    if i > 0:
        print('Warning: the above '+str(i)+' students have duplicate videos to grade.')

    # Sanity check: make sure we didn't assign any blank videos
    i = 0
    for student in students:
        if '' in student.videosToGrade or None in student.videosToGrade:
            i += 1
            print(student)
    if i > 0:
        print('Warning: the above '+str(i)+' students have been assigned blank videos.')


    # Sanity check: each student should have N videos to grade (or N copies of the "You did not upload a video..." text)
    i = 0
    for student in students:
        if len(student.videosToGrade) != N:
            i += 1
            print(student.webassignID+' has '+str(len(student.videosToGrade))+' videos to grade: should be '+str(N))
    if i > 0:
        print('Warning: the above '+str(i)+' students have the wrong number of videos to grade.')

    # Sanity check: make sure every video got assigned at least once
    assignedLinks = set([video for student in students for video in student.videosToGrade])
    if assignedLinks != set(students.videos):
        print('The following '+str(abs(len(students.videos)-len(assignedLinks)))+' videos didn\'t get assigned for grading: '+str([video for video in set(students.videos).difference(assignedLinks)]))

class studentList(list):

    def __init__(self,files, yndItems, likertItems, commentItems):

        self.R = 0
        self.grades=[]
        self.links = []
        self.videos = []
        self.fullNames = []
        self.webassignIDs = []
        self.comments = []
        # Read in the .csv file
        for filename in files:
            data = []
            with open(filename, 'rU') as csvfile:
                inputFile = csv.reader(csvfile, delimiter='\t', quotechar='|')
                for row in inputFile:
                    data.append(row)

            line = 0
            foundStart = False
            while not foundStart:    #Seek out the first line of student data
                if len(data[line]) >= 1:
                    if data[line][0] == 'Fullname':
                        foundStart = True
                line = line+1

            while line in range(len(data)):
                if len(data[line]) > 1: # Make sure we don't have a blank line
                    if data[line][0] != '': # Make sure we don't have one of the score lines
                        thisEntry = self.makeEntry(data[line], yndItems, likertItems, commentItems)
                        if thisEntry.webassignID not in self.webassignIDs:
                            self.append(thisEntry)
                            self.fullNames.append(thisEntry.fullName)
                            self.webassignIDs.append(thisEntry.webassignID)

                            # If any entry does not have a video link, then len(self.links) < len(self) and self.links[i] does not necessarily equal self[i].link
                            if thisEntry.link is not None and thisEntry.link is not '':
                                self.links.append(thisEntry.link)
                                if getYoutubeID(thisEntry.link) not in self.videos:
                                    self.videos.append(getYoutubeID(thisEntry.link))
                                else:
                                    print('WARNING: '+thisEntry.webassignID+' submitted the same video as '+self.find(getYoutubeID(thisEntry.link)).webassignID+': '+getYoutubeID(thisEntry.link))

                line += 1

    def makeEntry(self,row, yndItems, likertItems, commentItems):
        # Make it easy to extend the studentList class without having to retype __init__()
        return student(fullName=re.search('[^"].*[^"]',row[studentFullNameCol]).group(), webassignID=row[studentUserNameCol], link=row[studentLinkCol])

    def find(self,query):
        for entry in self:
            if query in (entry.fullName, entry.webassignID, entry.link, getYoutubeID(entry.link)):
                return entry
        print('No entry matches "'+query+'".')
        return student()

    def getValidLinks(self):
        # Return entries with valid links
        entries = []
        for entry in self:
            if entry.hasValidLink():
                entries.append(entry)
        return entries
    def readGrades(self, gradesFiles, yndItems, likertItems, commentItems):
        # Read in the tab-delimited grades file
        for filename in gradesFiles:
            data = []
            with open(filename, 'rU') as csvfile:
                inputFile = csv.reader(csvfile, delimiter='\t', quotechar='|')
                for row in inputFile:
                    data.append(row)
            

            line = 0

            questions = []
            foundStart = False
            while not foundStart:    #Seek out the first line of student data
                if len(data[line]) >= 1:
                    if data[line][0] == "Questions": # We can't always rely on Webassign ordering the questions correctly, so the order of the responses and the order of the IDs in student.videosToGrade won't always be the same. We fix that here.
                        for entry in data[line]:
                            if re.match('[0-9]',entry):    # Check to see if we've got a question number
                                questions.append(int(entry))
                        # The question numbers aren't guaranteed to be consecutive; we need to change each question number to its corresponding index of numerical order, e.g., [35,36,32] becomes [1,2,0]
                        orderedQuestions = copy(questions)
                        orderedQuestions.sort()
                        for i in range(len(questions)):
                            questions[i] = orderedQuestions.index(questions[i])


                    if data[line][0] == 'Fullname':
                        foundStart = True
                line = line+1

            # Down in the student grade data, now
            while line in range(len(data)):
                if len(data[line]) > 1: # Make sure we don't have a blank line
                    if data[line][0] != '': # Make sure we don't have one of the score lines
                        # Now we have a student in the grade file; find the right student in self
                        graderID = data[line][studentUserNameCol]

                        # Get the grades as one big ol' list of R*N ints or strings
                        collatedGrades = data[line][studentGradeCol:]
                        R = 10
                        if len(collatedGrades) != 90:
                            print(graderID+' has '+str(len(collatedGrades))+' responses; should be 90.')
                        # Webassign has '0' == Strongly Agree, '4' == Strongly Disagree. We need 5 == Strongly Agree, 1 == Strongly Disagree
                        for i in range(len(collatedGrades)):
                            if collatedGrades[i] != '':
                                if i <= len(collatedGrades):
                                    # In the data file, '0'=Yes, '1'=No, '2'=Difficult to Say:
                                    # we want 2=Yes, 1=Difficult to Say, 0=No
                                    # (should do this as cases)
                                    if (i)%R in yndItems:
                                        if collatedGrades[i] == '0':
                                            collatedGrades[i] = 3
                                        elif collatedGrades[i] == '2':
                                            collatedGrades[i] = 2                                
                                        elif collatedGrades[i] == '1':
                                            collatedGrades[i] = 1
                                    elif (i)%R in likertItems:
                                        try:
                                            collatedGrades[i] = 5-int(collatedGrades[i])
                                        except ValueError:
                                            print(graderID,collatedGrades[i],i)
                        # Okay, now that the conversion is done, starting at R-2 we remove every Rth element from collatedGrades (that's the "this video is better than mine" item)
                        # del collatedGrades[R-2::R]

                        # Sanity check; the number of total responses should be evenly divisible by the number of questions
                        student = self.find(graderID)
                        
                        if len(collatedGrades)%len(questions) != 0:
                            print('Wrong number of questions or graded responses! '+str(len(collatedGrades))+' '+str(len(questions))+' '+student.fullName)
                            
                        R = int(len(collatedGrades)/len(questions))   
                        # Cut the collatedGrades up into one chunk per question (with R entries)
                        for i in range(len(questions)):
                            j = questions.index(i)
                            if collatedGrades[j*R] != '':   # Check that the student actually graded that video
                                try:
                                    student.gradesGiven.append(videoGrade(yndItems, likertItems, commentItems, graderID=student.webassignID, videoID=student.videosToGrade[i], grade=collatedGrades[j*R:(j+1)*R]))
                                except:
                                    print(student.fullName+' grade assignment failed.')

                        # for i in range(len(questions)):
                        #     student.gradesGiven.append(studentGrade(graderID=student.webassignID, videoID = ))



                line += 1

    def distributeGrades(self):
        # Tally up all the grades for each video, and put them in student.gradesReceived
        for student in self:
            if student.hasValidLink():
                for grade in student.gradesGiven:
                    self.find(grade.videoID).gradesReceived.append(grade)

    def writeWebassignOutput(self, questionFile = 'question.txt', answerFile = 'answer.txt'):

        # WEBASSIGN QUESTION OUTPUT
        # =========================
        # Concatenate the grading assignments and write them to a file whose contents can be copy-pasted, in toto, to a Webassign assignment field.

        # WORKAROUND FOR WEBASSIGN MAX CODE LENGTH LIMIT
        # Webassign has a limit for how many characters can go in the question box; you won't see this limit until you actually put the question in an assignment and look at it from there. Aargh.
        # For ~200 students, we must put just the YouTube IDs in the database, not the whole youtu.be address. Keep the "You did not upload a video..." text for those who need it.
        for student in self:
            if student.hasValidLink():
                for link in student.videosToGrade:
                    student.videosToGrade.insert(0,getYoutubeID(student.videosToGrade.pop()))


        questionFile = open(questionFile,'w')
        questionFile.write('\
<eqn>\n\
#!/usr/bin/env perl\n\
%linkdb = (\n')
        for student in self:
            questionFile.write(student.getPerlLinksLine())
        questionFile.write(');\n\n')

        questionFile.write("sub get_link {\n\
    my ($stu, $linknum) = @_;\n\
    return $linkdb{$stu}[$linknum];\n\
}\n\
''\n\
</eqn>\n\
<eqn>\n\
$this_student = $STUDENT;  # We need to strip out the @\n\
$this_student =~ s/@/_/g;  # because that breaks hash lookup\n\
\n\
'';  # Make sure the output of this expression is blank\n\
</eqn>\n\n")

        questionFile.write('<b>Please watch and respond to the following video:</b> <a href=http://youtu.be/<EQN>get_link($this_student,$QUESTION_NUM-1);</EQN> target="_blank"><eqn get_link($this_student,$QUESTION_NUM-1);></a> (This might be your own video; if so, please grade it honestly!) <b>You will not receive any video links if you did not complete the extra credit assignment yourself.</b>\n<br><br>\n\n')

        questionFile.write("Does the video introduce the problem and state the main result?<_><SECTION>\n\
<br>\n\
Does the video identify the model(s) relevant to this physical system?<_><SECTION>\n\
<br>\n\
The computational model succeeds in modeling the video author's chosen physical system.<_><SECTION>\n\
<br>\n\
The presenter successfully connects his/her model to the experimental data.<_><SECTION>\n\
<br>\n\
The presentation in the video is clear and easy to follow.<_><SECTION>\n\
<br>\n\
This video lab report is better than mine.<_><SECTION>\n\
<br>\n\
<b>If you have comments about the video not covered by the rubric, please write them below.</b><br><_><SECTION>")

        questionFile.close()

        # WEBASSIGN ANSWER OUTPUT
        # =======================
        # The first 2 answers are Yes/No/Hard to Tell, the next 4 are 5-point Likert Scale, and then the comment box is a comment box.
        answerFile = open(answerFile,'w')
        for i in range(2):
            if i != 0:
                answerFile.write('<SECTION>\n')
            answerFile.write("<eqn $ORDERED=3; ''>Yes\n\
Difficult to Say\n\
No\n")
        for i in range(self.R-3):
            answerFile.write('<SECTION>\n')
            answerFile.write("<eqn $ORDERED=3; ''>Strongly Agree\n\
Agree\n\
Neutral\n\
Disagree\n\
Strongly Disagree\n")
        answerFile.write('<SECTION>\nThere is no wrong answer.')

        answerFile.close()

class expertList(studentList):
    # This differs from the studentList class only in that each element is an expert object, not a student object
    def makeEntry(self,row, yndItems, likertItems, commentItems):
        # print(len(row[gradeCol:]))
        self.grades.append(videoGrade(yndItems, likertItems, commentItems,graderID = 'expert',videoID=row[expertFullNameCol],grade = row[gradeCol:]))
        return expert(yndItems, likertItems, commentItems, fullName=re.search('[^"].*[^"]',row[expertFullNameCol]).group(),webassignID=row[expertUserNameCol],link=row[expertLinkCol],grade=row[gradeCol:])

class student:

    def __init__(self, fullName=None, webassignID=None, link=None):
        self.fullName = fullName
        self.webassignID = webassignID
        self.link = getYoutubeLink(link)
        self.video = getYoutubeID(link)
        self.calibration = []
        self.videosToGrade = []
        self.calibrated = False
        self.gradesGiven = []
        self.gradesReceived = []

        self.finalGrade = 0
        self.finalGradeVector = []
    def __repr__(self):
        return str(self.fullName + ', ' + str(self.link))

    def hasValidLink(self):
        if self.link is not '' and self.link is not None:
            return True
        return False

    def perlPerson(self):   # Generate a Perl-safe STUDENT ID (i.e. no @ sign)
        return re.sub('@','_',self.webassignID);

    def getPerlLinksLine(self):
        outstring = '\t\"' + self.perlPerson() + '\"=> [ ';
        for video in self.videosToGrade:
            outstring += '\"' + video +'\", ';
        outstring += '],\n';
        return outstring

    def flaggedForReview(self):
        for grade in self.gradesReceived:
            if set(grade.grade) == {3}:  # If any student graded a video as all-neutral, that indicates the video might have had technical difficulties
                return True
        return False

    def calibrate(self, experts, exclusions):
        if len(self.gradesGiven) > 0:
            # Find the normalized R-dimensional calibration vector
            myCalibratedGrades = [grade for grade in self.gradesGiven if grade.videoID in experts.videos]
            # myCalibratedGrades = [grade[i] for grade in self.gradesGiven]
            # self.calibration = 'Calibrated with '+str(len(myCalibratedGrades))+' videos.'
            self.calibration = calibration(myCalibratedGrades,[expert.grade for expert in experts],exclusions)
            self.calibrated = True


class expert(student):
    # The experts will select and grade a few students' videos, then concatenate those 
    def __init__(self, yndItems, likertItems, commentItems, fullName=None, webassignID=None, link=None, grade=None):
        self.fullName = fullName
        self.link = getYoutubeLink(link)
        self.videoID = getYoutubeID(link)
        self.webassignID = webassignID
        self.grade = videoGrade(yndItems, likertItems, commentItems, graderID='expert',videoID=self.videoID, grade=grade)

class videoGrade(list):

    def __init__(self, yndItems, likertItems, commentItems, graderID=None, videoID=None, grade=[]):
        self.graderID = graderID
        self.videoID = getYoutubeID(videoID)
        self.comments = [grade[3],grade[5],grade[7],grade[9]]
        for item in grade:
            # print(graderID+' '+str(grade.index(item))+': '+str(item))
            if grade.index(item) not in [3,5,7,9]:
                self.append(float(item))
                
        #     except ValueError:
        #         self.comment = item

    def __repr__(self):
        return 'Grader: '+str(self.graderID)+', Video ID: '+str(self.videoID)+', Grade: '+str([num for num in self])

class calibration(list):
    def __init__(self, studentGrades, expertGrades, exclusions):
        if len(studentGrades) == 0:
            return None

        # Sort both lists of grades by VideoID
        studentGrades = sorted(studentGrades, key=lambda grade: grade.videoID)
        expertGrades = sorted(expertGrades, key=lambda grade: grade.videoID)

        self.differenceVectors=[]
        # myNums = [num for grade in studentGrades for num in grade]
        # expNums = [num for grade in expertGrades for num in grade]
        myNums = []
        expNums = []
        for grade in studentGrades:
            for i in range(len(grade)):
                if i not in exclusions:
                    myNums.append(grade[i])
        for grade in expertGrades:
            for i in range(len(grade)):
                if i not in exclusions:
                    expNums.append(grade[i])
        # Screw it, just get the alignment and the difference in magnitude
        self.dotProduct = 0
        for i in range(len(myNums)):
            self.dotProduct += myNums[i]*expNums[i]
        self.alignment = self.dotProduct/(np.linalg.norm(myNums)*np.linalg.norm(expNums))

        self.normDiff = np.linalg.norm(myNums) - np.linalg.norm(expNums)

        self.weight = self.alignment**(abs(1*self.normDiff))
        # self.weight=0.1