import nltk

nltk.data.path=['.\\nltk_data']
#print(nltk)
#nltk.tree.demo()
def main():
	testStr=[]
	testStr.append("this project entails building a match-making website for students projects, like the capstone project you’re bidding on.")
	testStr.append("a nice interface for two different stakeholders, namely (a) project providers, such as faculty and NGOs, and (b) project seekers, such as students. We will need to interview stakeholders and create a requirements document describing the needed elements.")
	testStr.append("a database to save the information and metadata created by item 1. We will need to figure out what type of database to use (SQL, noSQL, …) and design the schema for the database.")
	testStr.append("an algorithm for matching the two stakeholders. We will need to define metrics and use existing (or develop new) algorithms that attempt to optimize such metrics; for example, maximize happiness of all stakeholders, minimize extra effort, maximize learning, etc. The metrics may be multi criteria (that is, more than one metric, with weights.")
	for line in testStr:
		tokenArray=nltk.word_tokenize(line)
		print("\nTHE SENTENCE:\n"+str(tokenArray)+"\n\n")
		nouns=[]
		adjectives=[]
		for word,type in nltk.pos_tag(tokenArray):
			if(type=='NN' or type=='NNP' or type=='NNS' or type=='NNPS'):
				nouns.append(word)
			elif(type=='JJ' or type == 'JJR' or type=='JJS'):
				adjectives.append(word)
		print("\nJust the nouns: \n"+str(nouns)+"\n")
		print("\nJust the adjectives: \n"+str(adjectives)+"\n")
	
main()