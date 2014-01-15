import sys
#takes in information from the webparser. Insert arguments as a list, which should be: [question number, question, evaluator response, comments]
#*Make sure to use finish() to close out of the document*

class htmlOutput:
	def __init__(self, labNumber):
		self.file=open("./lab" + str(labNumber) + ".html" , "wt")
		self.file.write(
"""<b>This is how the course instructors evaluated this video. Please compare your own responses to the instructors' responses:</b>
<br><br>
<table>
    <tbody>
        <tr>
            <td width="3%">#</td>
            <td width="37%">Assessment Item</td>
            <td width="60%">Instructors' Response</td>
        </tr>""")
	
	def addItem(self, item):
		if len(item) != 4:
			sys.exit("only three items in evaluator assessment. input : " + item)
			
		self.file.write("""\n
		<tr>
			<td>""" + str(item[0]) + """</td>
			<td><b>""" + str(item[1]) + """</b>
			</td>
			<td><b>""" + str(item[2]) + """</b>""" + str(item[3]) + """<br><br></td>
		</tr>""")
	def finish(self):
		self.file.write("""
		
	</tbody>
</table>""")	
	
		self.file.close()
  
if False:  
	#this will create lab2.html in current directory
	z = htmlOutput(2)
	z.addItem([1, "The video presentation is clear and easy to follow.", "STRONGLY AGREE", "The student does an excellent job highlighting what he is talking about through zooming, highlighting with animated boxes, and clearly speaking."])
	z.addItem([2, "Does the video introduce the problem and state the main result?", "HARD TO TELL", "He has done a better job than the previous videos, but it still need more work so that a person who doesn't know anything about this lab can still have a clear picture about what's going on in the lab from the beginning of the presentation."])
	z.finish()


