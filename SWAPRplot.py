from sqlite1 import *
import matplotlib.pyplot as plt
from SWAPRgrades import *
from scipy.stats.stats import pearsonr, linregress

labNumber = 3
# Make histograms!
db = SqliteDB("2211 Fall 2013 Public.db")
maxScore = getMaxScore(db,labNumber)

# # Get the item scores

db.cursor.execute("SELECT finalGradeVector, rawGradeVector FROM grades WHERE labNumber = ? and finalGrade != 0",[labNumber])
gradesData = [ [stringToList(datum[0]), stringToList(datum[1])] for datum in db.cursor.fetchall()]


item1raw = [float(datum[1][0]) for datum in gradesData]
item2raw = [float(datum[1][1]) for datum in gradesData]
item3raw = [float(datum[1][2]) for datum in gradesData]
item4raw = [float(datum[1][3]) for datum in gradesData]
item5raw = [float(datum[1][4]) for datum in gradesData]
item6raw = [float(datum[1][5]) for datum in gradesData]

rawScores = [item1raw,item2raw,item3raw,item4raw,item5raw,item6raw]


item1calibrated = [float(datum[0][0]) for datum in gradesData]
item2calibrated = [float(datum[0][1]) for datum in gradesData]
item3calibrated = [float(datum[0][2]) for datum in gradesData]
item4calibrated = [float(datum[0][3]) for datum in gradesData]
item5calibrated = [float(datum[0][4]) for datum in gradesData]
item6calibrated = [float(datum[0][5]) for datum in gradesData]

calibratedScores = [item1calibrated,item2calibrated,item3calibrated,item4calibrated,item5calibrated,item6calibrated]

db.cursor.execute("SELECT weight1, weight2, weight3, weight4, weight5, weight6 FROM weightsBIBI where labNumber = ?",[labNumber])

weightsData = [ datum for datum in db.cursor.fetchall() ]

weight1 = [float(datum[0]) for datum in weightsData]
weight2 = [float(datum[1]) for datum in weightsData]
weight3 = [float(datum[2]) for datum in weightsData]
weight4 = [float(datum[3]) for datum in weightsData]
weight5 = [float(datum[4]) for datum in weightsData]
weight6 = [float(datum[5]) for datum in weightsData]

weights = [weight1,weight2,weight3,weight4,weight5,weight6]

# print(len(data))
# db.cursor.execute("SELECT weightSum from weightsBIBI where labnumber = 3")
# grades = [float(grade[0])*100/6 for grade in db.cursor.fetchall()]
# plt.hist(grades,histtype='stepfilled',bins=19)
# plt.title('Lab 3 (Public) Calibration Grades')
# plt.xlim([0,100])
# plt.ylim([0,30])
# plt.xlabel('Grade')
# plt.ylabel('Number of Students')
# plt.show()

# Item-by-item plot
if True:
    fig = plt.figure(figsize=(10,10))
    fig.suptitle("Lab "+str(labNumber)+" (Public)")
    plt.figtext(0.05,0.5,'Number of Responses',rotation=90)
    plt.figtext(0.95,0.5,'Number of Students',rotation=90)


    for i in range(6):
    # Item Scores
        ax = fig.add_subplot(6,2,2*i+1)
        # ax.subplot(6,2,2*i + 1)
        ax.hist(calibratedScores[i],histtype='stepfilled',bins=20,label=['Calibrated'])
        ax.hist(rawScores[i],histtype='step',bins=20,color=['black'],label=['Uncalibrated'])
        ax.set_ylabel('#'+str(i+1),rotation=0)
        ax.yaxis.set_label_position('right')
        if i == 0:
            ax.legend(loc='upper left')
            ax.set_title('Item Scores')
        ax.set_xlim([0,max(rawScores[i])])
        if i == 5:
            ax.set_xlabel('Peer Score')
            ax.set_xticklabels([0,'','','','','','Max'])
        else:
            ax.set_xticklabels([])
        if i in [1,2]:
            ax.set_ylim([0,100])
            ax.set_yticks([0,100])
        else:
            ax.set_ylim([0,40])
            ax.set_yticks([0,40])

        # Item Weights
        ax = fig.add_subplot(6,2,2*i+1+1)
        # plt.subplot(6,2,2*i + 1 + 1)
        ax.hist(weights[i],histtype='stepfilled',bins=4,color=['green'])
        if i == 0:
            ax.set_title('Item Weights')
        ax.set_xlim([0,1])
        ax.set_ylim([0,70])
        ax.set_yticks([0,70])
        ax.yaxis.tick_right()
        if i == 5:
            ax.set_xlabel('Weight')
        else:
            ax.set_xticklabels([])

    plt.subplots_adjust( wspace = 0.1)
    plt.show()

