from sqlite1 import *
import matplotlib.pyplot as plt
from SWAPRgrades import *
from scipy.stats.stats import pearsonr, linregress
from numpy import *
from SWAPRstrings import *
import math

labNumber = 1
group = 'Campus'
# Make histograms!
db = SqliteDB("PHYS 2211 Fall 2013 "+group+".db")
maxScore = getMaxScore(db,labNumber)

def autolabel(rects):
# attach some text labels
    for ii,rect in enumerate(rects):
        height = rect.get_height()
        plt.text(rect.get_x()+rect.get_width()/2., 1.02*height, '%s'% (name[ii]),
                ha='center', va='bottom')

def getExpertURLs(filename):
    with open(filename,'r') as expertFile:
        expertURLs = []
        for line in expertFile:
            if line.split('\t')[0] != 'Fullname':
                expertURLs.append(getYoutubeLink(line.split('\t')[2]))
    return expertURLs


# # Get the item scores
if True:
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

if False:
    # db.cursor.execute("SELECT URL FROM experts WHERE labNumber = ?",[labNumber])
    expertURLs = getExpertURLs('Lab'+str(labNumber)+'Experts.txt')
    # print(expertURLs)
    totalResponses = []
    for URL in expertURLs:
        rubricGradedDict = getRubricGradedDict(db,labNumber)
        db.cursor.execute("SELECT response FROM responses WHERE URL = ? AND labNumber = ?",[URL, labNumber])
        responses = []
        for entry in db.cursor.fetchall():
            response = stringToList(str(entry[0]))
            tempResponse = []
            for i in range(len(response)):
                if rubricGradedDict[i+1]:
                    try:
                        tempResponse.append(int(response[i]))
                    except:
                        break
            if len(tempResponse) == 6:
                responses.append(tempResponse)
        db.cursor.execute("SELECT grade FROM experts WHERE URL = ?",[URL])
        expertGradeTemp = stringToList(str(db.cursor.fetchone()[0]))
        expertGrade = [int(round(float(entry))) for entry in expertGradeTemp]
        # print(expertGradeTemp)
        totalResponses.append([URL,responses,expertGrade])
    
    # print(totalResponses)
                
# print(rubricGradedDict)

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

# print(totalResponses[1][1])

# Item-by-item plot
if True:
    fig = plt.figure(figsize=(20,100))
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

# Raw responses item-by-item plot
if False:
    for labNumber in [1,2,3,4]:
        for group in ['Campus']:
            print('Plotting Lab '+str(labNumber)+' '+group+'...')

            db = SqliteDB("PHYS 2211 Fall 2013 "+group+".sqlite")

            expertURLs = getExpertURLs('Lab'+str(labNumber)+'Experts.txt')
            # print(expertURLs)
            totalResponses = []
            for URL in expertURLs:
                rubricGradedDict = getRubricGradedDict(db,labNumber)
                db.cursor.execute("SELECT response FROM responses WHERE URL = ? AND labNumber = ?",[URL, labNumber])
                responses = []
                for entry in db.cursor.fetchall():
                    response = stringToList(str(entry[0]))
                    tempResponse = []
                    for i in range(len(response)):
                        if rubricGradedDict[i+1]:
                            try:
                                tempResponse.append(int(response[i]))
                            except:
                                break
                    if len(tempResponse) == 6:
                        responses.append(tempResponse)
                db.cursor.execute("SELECT grade FROM experts WHERE URL = ?",[URL])
                expertGradeTemp = stringToList(str(db.cursor.fetchone()[0]))
                expertGrade = [int(round(float(entry))) for entry in expertGradeTemp]
                # print(expertGradeTemp)
                totalResponses.append([URL,responses,expertGrade])

            ymax = 1
            fig = plt.figure(figsize=(11,11))
            fig.suptitle("Lab "+str(labNumber)+" Raw Responses ("+group+")")
            # plt.figtext(0.05,0.5,'Number of Responses',rotation=90)
            plt.figtext(0.95,0.5,'Proportion of Students',rotation=90)


            # Cycle over each rubric item (columns) with 5 expert videos apiece (rows)
            for i in range(6):
                for j in range(5):
                    ax = fig.add_subplot( 5,6, (i+1)+( 6*(j) ) )
                    expertScore = totalResponses[j][2][i]
                    ax.scatter(expertScore,0,c='k',s=400,marker='^',label='Expert Score')
                    ax.set_xlim([-0.5,4.5])
                    ax.set_ylim([0,ymax])
                    ax.set_xticklabels([])
                    ax.set_yticklabels([])
                    ax.set_yticks([])
                    ax.yaxis.tick_right()

                    data = [score[i] for score in totalResponses[j][1]]
                    N = len(data)
                    stdevFromMean = std(data)
                    stdevFromExpert = math.sqrt( mean( [(score - expertScore)**2 for score in data] ) )
                    ax.text(-0.45,0.95,'StDM='+str('%.3f' % stdevFromMean)+'\nStDE='+str('%.3f' % stdevFromExpert),verticalalignment='top')

                    if i == 5:  # Rightmost column
                        ax.set_yticks([0,ymax])
                        ax.set_yticklabels([0,ymax])
                    if i in [1,2] or (i == 3 and labNumber == 3):   # Y-HtT-N Items
                        ax.set_xlim([-0.5,2.5])
                        ax.set_xticks([0,1,2])
                        bars = ax.hist(data,histtype='stepfilled',bins=[-0.5,0.5,1.5,2.5],alpha=0.3,normed=True)
                        if j == 4:  # Bottom Row
                            ax.set_xticklabels(['Yes','HtT','No'])
                    else:
                        bars = ax.hist(data,histtype='stepfilled',bins=[-0.5,0.5,1.5,2.5,3.5,4.5],alpha=0.3,normed=True)
                        ax.set_xticks([0,1,2,3,4])
                        if j == 4:
                            ax.set_xticklabels(['SA','A','N','D','SD'])

                    if i == 0:  # Leftmost column
                        if j in [0,1]:  # Practice videos
                            titlePrefix = 'Practice '+str(j+1)
                        else:
                            titlePrefix = 'Calibration '+str(j+1 -2)
                        title = titlePrefix+"\n"+getYoutubeID(totalResponses[j][0])
                        if j == 4:  # Hidden calibration video
                            title += "\n(hidden)"
                        title += "\nN = "+str(N)
                        ax.set_ylabel(title, rotation=0)

                    if j == 0:  # Bottom row
                        ax.set_title("Item #"+str(i+1))
                    # print(bars[1])
                    for k in range(len(bars[0])):
                        ax.text((bars[1][k+1]+bars[1][k])/2,min([bars[0][k]+0.05,0.6]),str('%.2f' % bars[0][k]).lstrip('0'),horizontalalignment='center')
                        # ax.legend(loc='lower',prop={'size':12})
            plt.subplots_adjust( wspace = 0.1)
            plt.figtext(0.5,0.025,"StDM = Stndard Deviation from the Mean, StDE = Standard Deviation from Expert Score\n(black triangles mark expert scores)",horizontalalignment='center')
            # plt.savefig('/Users/Scott/Google Drive/Physics MOOC Sync/gtMOOC Grades & Data/SWAPR Figures/Raw Responses/Lab '+str(labNumber)+' '+group+'.png')
            # plt.show()
            print('Done.')

# Student responses vs. expert responses
if False:
    group = 'Campus'
    # labNumber = 1
    db = SqliteDB("2211 Fall 2013 "+group+".db")

    # print(expertURLs)
    likert5pairs = []
    yhnPairs = []
    for labNumber in [1,2,3]:
        totalResponses = []
        expertURLs = getExpertURLs('Lab'+str(labNumber)+'Experts.txt')
        # for URL in expertURLs:
        URL = expertURLs[-1]
        rubricGradedDict = getRubricGradedDict(db,labNumber)
        db.cursor.execute("SELECT response FROM responses WHERE URL = ?",[URL])
        responses = []
        for entry in db.cursor.fetchall():
            response = stringToList(str(entry[0]))
            tempResponse = []
            for i in range(len(response)):
                if rubricGradedDict[i+1]:
                    try:
                        tempResponse.append(int(response[i]))
                    except:
                        break
            if len(tempResponse) == 6:
                responses.append(tempResponse)
        db.cursor.execute("SELECT grade FROM experts WHERE URL = ?",[URL])
        expertGradeTemp = stringToList(str(db.cursor.fetchone()[0]))
        expertGrade = [int(round(float(entry))) for entry in expertGradeTemp]
        # print(expertGradeTemp)
        totalResponses.append([URL,responses,expertGrade])
        # We'll be treating the 5- and 3-item questions differently

        # rubricTypes = getRubricTypesDict(db,labNumber)

        for entry in totalResponses:
            for i in range(len(entry[2])):
                for studentResponse in entry[1]:
                    if i in [1,2] or (i == 3 and labNumber == 3):
                        try:
                            yhnPairs.append( [entry[2][i], studentResponse[i]] )
                        except:
                            pass
                    else:
                        try:
                            likert5pairs.append( [entry[2][i], studentResponse[i]] )
                        except:
                            pass
    # fig = plt.figure(figsze = (8,8))
    x = [pair[0] for pair in likert5pairs]  # Expert scores
    y = [pair[1] for pair in likert5pairs]  # Student scores
    H, xedges, yedges = histogram2d(x,y,bins=[[-0.5,0.5,1.5,2.5,3.5,4.5],[-0.5,0.5,1.5,2.5,3.5,4.5]], normed=True)

    # print(x,y)
    # H.shape, xedges.shape, yedges.shape
    extent = [0,5,0,5]
    plt.imshow(H, extent=extent, interpolation='nearest',origin='lower')
    N = len(likert5pairs)
    R,P = pearsonr(x,y)
    plt.suptitle("Likert5 Responses (Hidden Calibration Videos) (Campus)\nN="+str(N)+", Pearson's R="+str('%0.3f'%R)+', P-val='+str('%0.3f' % P))
    plt.xlabel('Expert Score')
    plt.ylabel('Student Score')
    # plt.figtext(0.5,0.1,'Blarg!')
    plt.colorbar()
    plt.show()

# Histogram sorted by expert score
if False:
    for group in ['Public','Campus']:
        likert5pairs = []
        yhnPairs = []
        for labNumber in [1,2,3]:
            totalResponses = []
            print('Querying Lab '+str(labNumber)+' '+group+'...')

            db = SqliteDB("2211 Fall 2013 "+group+".db")

            expertURLs = getExpertURLs('Lab'+str(labNumber)+'Experts.txt')
            # print(expertURLs)
            for URL in expertURLs:
                rubricGradedDict = getRubricGradedDict(db,labNumber)
                db.cursor.execute("SELECT response FROM responses WHERE URL = ?",[URL])
                responses = []
                for entry in db.cursor.fetchall():
                    response = stringToList(str(entry[0]))
                    tempResponse = []
                    for i in range(len(response)):
                        if rubricGradedDict[i+1]:
                            try:
                                tempResponse.append(int(response[i]))
                            except:
                                break
                    if len(tempResponse) == 6:
                        responses.append(tempResponse)
                db.cursor.execute("SELECT grade FROM experts WHERE URL = ?",[URL])
                expertGradeTemp = stringToList(str(db.cursor.fetchone()[0]))
                expertGrade = [int(round(float(entry))) for entry in expertGradeTemp]
                # print(expertGradeTemp)
                totalResponses.append([URL,responses,expertGrade])



            for entry in totalResponses:
                for i in range(len(entry[2])):
                    for studentResponse in entry[1]:
                        if i in [1,2] or (i == 3 and labNumber == 3):
                            try:
                                yhnPairs.append( [entry[2][i], studentResponse[i]] )
                            except:
                                pass
                        else:
                            try:
                                likert5pairs.append( [entry[2][i], studentResponse[i]] )
                            except:
                                pass

        ymax = 1
        # fig = plt.figure(figsize=(15,4))
        # fig.suptitle("Lab "+str(labNumber)+" Raw Responses ("+group+")")
        # plt.figtext(0.05,0.5,'Number of Responses',rotation=90)
        # plt.figtext(0.95,0.5,'Proportion of Students',rotation=90)
        likert5sortedByExpertScore = [[],[],[],[],[]]
        yhnSortedByExpertScore = [[],[],[]]
        for pair in yhnPairs:
            yhnSortedByExpertScore[pair[0]].append(pair[1])
        for pair in likert5pairs:
            likert5sortedByExpertScore[pair[0]].append(pair[1])
        print(len(likert5sortedByExpertScore))
        for dataSet in [likert5sortedByExpertScore,yhnSortedByExpertScore]:
        # Cycle over each rubric item (columns) with 5 expert videos apiece (rows)
        # for i in range(5):
            if len(dataSet) == 5:
                fig = plt.figure(figsize=(15,4))
            elif len(dataSet) == 3:
                fig = plt.figure(figsize=(9,4))
            
            for i in range(len(dataSet)):
                expertScore = i
                # data = likert5sortedByExpertScore[expertScore]
                data = dataSet[expertScore]
                if len(dataSet) == 5:
                    ax = fig.add_subplot( 1,5,i+1 )
                    ax.set_xlim([-0.5,4.5])
                    bars = ax.hist(data,histtype='stepfilled',bins=[-0.5,0.5,1.5,2.5,3.5,4.5],alpha=0.3,normed=True)
                    ax.set_xticks([0,1,2,3,4])
                    ax.set_xticklabels(['SA','A','N','D','SD'])
                    ax.set_title("Expert Response: "+str(['SA','A','N','D','SD'][i]))
                    plt.suptitle('Likert5 Response Distributions (Labs 1-3) ('+group+')')
                elif len(dataSet) == 3:
                    ax = fig.add_subplot( 1,3,i+1 )
                    ax.set_xlim([-0.5,2.5])
                    bars = ax.hist(data,histtype='stepfilled',bins=[-0.5,0.5,1.5,2.5],alpha=0.3,normed=True)
                    ax.set_xticks([0,1,2])
                    ax.set_xticklabels(['Yes','HtT','No'])
                    ax.set_title("Expert Response: "+str(['Yes','HtT','No'][i]))
                    plt.suptitle('Y-HtT-N Response Distributions (Labs 1-3) ('+group+')')
                ax.set_ylim([0,1])
                ax.set_xticklabels([])
                ax.set_yticklabels([])
                ax.set_yticks([])
                ax.yaxis.tick_right()
                ax.set_xlabel('Student Response')

                N = len(data)
                stdevFromMean = std(data)
                stdevFromExpert = math.sqrt( mean( [(score - expertScore)**2 for score in data] ) )
                ax.text(-0.45,0.95,'N='+str(N)+'\nStDM='+str('%.3f' % stdevFromMean)+'\nStDE='+str('%.3f' % stdevFromExpert),verticalalignment='top')

                if i == 4:  # Rightmost column
                    ax.set_yticks([0,ymax])
                    ax.set_yticklabels([0,ymax])
                    ax.yaxis.set_label_position('right')
                    ax.set_ylabel("Proportion of Students")
                for k in range(len(bars[0])):
                    ax.text((bars[1][k+1]+bars[1][k])/2,min([bars[0][k]+0.025,0.65]),str('%.2f' % bars[0][k]).lstrip('0'),horizontalalignment='center')
                    # ax.legend(loc='lower',prop={'size':12})
            plt.subplots_adjust( bottom = 0.2, top=0.8)
            plt.figtext(0.5,0.025,"StDM = Standard Deviation from the Mean, StDE = Standard Deviation from Expert Score",horizontalalignment='center')
            if len(dataSet) == 5:
                saveString = 'Likert5'
            elif len(dataSet) == 3:
                saveString = 'yhn'
            plt.savefig('/Users/Scott/Google Drive/Physics MOOC Sync/gtMOOC Grades & Data/SWAPR Figures/Responses by Expert Response/'+saveString+'Responses'+group+'.png')

            # plt.show()
        print('Done with '+group+'.')