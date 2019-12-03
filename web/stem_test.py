
# import these modules 
from nltk.stem import PorterStemmer 
from nltk.tokenize import word_tokenize 
import re
import string
   
ps = PorterStemmer() 
  
# choose some words to be stemmed 
words = ["flask", "java", "steelers", "microservice", "architectural"] 
temp = str("A principle of the Unix philosophy is “do one thing and do it well”. This is a tenet embodied by the increasingly popular microservice architectural style. The microservice model is commonly associated with the “back-end” of an application. In this style of architecture, the logic behind an application is composed from independent and tightly-coupled microservice pieces.")
punct = "!\"#$%&()*+,-./:;<=>?@[\]^_`{|}~”“"
temp = temp.translate(str.maketrans('', '', punct))
print(temp)

tokens = None
if temp:
	tokens = temp.split(" ")
for t in tokens:
	print(t)
  