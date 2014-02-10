from SWAPRsqlite import *
from SWAPRstrings import *

def exportWebassign(filename,db,labNumber):

    db.cursor.execute("SELECT DISTINCT wID FROM assignments WHERE labNumber = ?",[labNumber])
    wIDs = [str(item[0]) for item in db.cursor.fetchall()]

    db.cursor.execute("SELECT count(DISTINCT URL) FROM experts WHERE labNumber = ? AND NOT hidden",[labNumber])
    evalStartIndex = int(db.cursor.fetchone()[0]) # The webassign evaluation assignment will contain URLs from getURLsToGrade starting with the evalStartIndex-th entry; this excludes the practice and unhidden calibration videos
    print('evalStartIndex='+str(evalStartIndex))

    with open(filename,'w') as output:
        output.write('<eqn>\n'
            '#!/usr/bin/env perl\n'
            '%linkdb = (\n')

        for wID in wIDs:
            # if db.getURL(wID,labNumber) not in ['',None]:
            output.write(getPerlLinksLine(wID,db.getURLsToGrade(wID,labNumber)[evalStartIndex:]))
        output.write(');\n\n')

        output.write('sub get_link {\n'
            'my ($stu, $linknum) = @_;\n'
            'if ($linkdb{$stu}[$linknum]) {'
            'return $linkdb{$stu}[$linknum];\n'
            '} else {\n'
            'return $linkdb{"default"}[$linknum]}\n'
            "}\n''\n"
            '</eqn>\n'
            '<eqn>\n'
            '$this_student = $STUDENT;'  # We need to strip out the @
            '$this_student =~ s/@/_/g;'  # because that breaks hash lookup
            '\n'
            "'';"  # Make sure the output of this expression is blank
            '</eqn>\n\n')

        output.write('<b>Please watch and respond to the following video:</b> <a href=http://youtu.be/<EQN>get_link($this_student,$QUESTION_NUM-1);</EQN> target="_blank"><eqn get_link($this_student,$QUESTION_NUM-1);></a> (This might be your own video; if so, please grade it honestly!)\n<br><br>\n\n')

def writeCommentsWebassign(db,filename,labNumber):

    with open(filename,'w') as output:
            output.write('<eqn>\n'
                '#!/usr/bin/env perl\n'
                '%comments_db = (\n')
            typeDict = getRubricTypeDict(db,labNumber)

            db.cursor.execute("SELECT wID FROM submissions")
            wIDs = [str(d[0]) for d in db.cursor.fetchall()]



            for wID in wIDs:
                  db.cursor.execute("SELECT grade FROM grades, submissions WHERE submissions.Lab"+str(labNumber)+"URL = grades.URL AND submissions.wID = ?",[wID])
                  responses = [stringToList(str(d[0])) for d in db.cursor.fetchall()]
                  if len(responses) > 0:
                        peerComments = []
                        for response in responses:
                              comments = [str(item).replace('"',"'") for item in response if typeDict[response.index(item) +1] == 'freeResponse'] # Everything in the database is 1-indexed
                              peerComments.append(comments)
                        i = 0
                        # Construct the string of all comments for this wID
                        perlString = ''
                        for comments in peerComments:
                              perlString += "Item "+str(i+1)+": "+comments[i]
                              # for comment in comments:
                              #       perlString += "Item "+str(comments.index(comment)+1)+": "+comment+"<br>"
                              perlString += '<br><br>'
                              
                        output.write( '"' + perlPerson(wID) + '"=>{ "comments"=>"'+perlString+'"},\n' )
            
            output.write(');\n\n')

            output.write('# END link DB definition\n'
                        '#==============================\n'

                        'sub get_comments{\n'
                        'my ($stu) = @_;\n'
                        "return $comments_db{$stu}{'comments'};\n"
                        '}\n'

                        '$this_student = $STUDENT; #we need to strip out the @\n'
                        '$this_student =~ s/@/_/g; #cause that breaks hash lookup\n'
                        "''; #make sure the output of this expression is blank\n"
                        '</eqn>\n'
                        
                        '<EQN get_comments($this_student);>')
