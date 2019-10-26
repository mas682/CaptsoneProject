import nltk
import psycopg2
nltk.data.path=['.\\nltk_data']


#demo of nltk library: natural language processing 
def demo_nltk():
	testStr=[]
	testStr.append("this project entails building a match-making website for students projects, like the capstone project you’re bidding on.")
	testStr.append("a nice interface for two different stakeholders, namely (a) project providers, such as faculty and NGOs, and (b) project seekers, such as students. We will need to interview stakeholders and create a requirements document describing the needed elements.")
	testStr.append("a database to save the information and metadata created by item 1. We will need to figure out what type of database to use (SQL, noSQL, …) and design the schema for the database.")
	testStr.append("an algorithm for matching the two stakeholders. We will need to define metrics and use existing (or develop new) algorithms that attempt to optimize such metrics; for example, maximize happiness of all stakeholders, minimize extra effort, maximize learning, etc. The metrics may be multi criteria (that is, more than one metric, with weights.")
	for line in testStr:
		tokenArray=nltk.word_tokenize(line)
		taggedArray=nltk.pos_tag(tokenArray)
		#print("\nTHE SENTENCE:\n"+str(tokenArray)+"\n\n")
		print("\nTagged sentence: \n"+str(taggedArray)+"\n\n\n\n\n\n");
		tags=[]
		for word,type in taggedArray:
			if(type=='NN' or type=='NNP' or type=='NNS' or type=='NNPS'):
				noun=word
				startFrom=tokenArray.index(word)
				#print(startFrom)
				for x in range(startFrom-1,0,-1):
					prevWord=taggedArray[x]
					#print("prevword : "+str(prevWord))
					if(prevWord[1]=='JJ' or prevWord[1] == 'JJR' or prevWord[1]=='JJS'
						or prevWord[1]=='NN' or prevWord[1]=='NNP' or prevWord[1]=='NNS' or prevWord[1]=='NNPS'):
						noun=prevWord[0]+" "+noun
						#print("prev added")
					else:
						break
				for x in range(startFrom+1, len(tokenArray)):
					afterWord=taggedArray[x]
					#print("afterword : "+str(afterWord))
					if(afterWord[1]=='JJ' or afterWord[1] == 'JJR' or afterWord[1]=='JJS'
						or afterWord[1]=='NN' or afterWord[1]=='NNP' or afterWord[1]=='NNS' or afterWord[1]=='NNPS'):
						noun=noun + " "+afterWord[0]
						#print("after added")
					else:
						break
				tags.append(noun)
		tags=list(dict.fromkeys(tags))
		print("\nTags:"+str(tags))
		
#demo of using psycopg2 library; postgresql connector
def sql():
	print("enter username")
	un=input()
	print("enter password")
	pw=input()
	con=psycopg2.connect(database="postgres",user=un,password=pw,host="localhost",port="5432")
	executor=con.cursor()
	executor.execute(
	'''
	SELECT * FROM searchProjects('CS');
	''')
	returned=executor.fetchall()
	numRow=len(returned[0])
	print("number of rows: ", numRow)
	for row in returned:
		for column in range(numRow):
			print(row[column])
	
	
def main():
	demo_nltk()
	#sql()
	

main()