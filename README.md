JSON PARSER PROGRAM - README
Author: Nate Briand

Instructions:
Ready to be used is the main program and sub folders which contain
various test files already implemented. Inside 'input.folder' contains 10 test files.
7 test files, labeled Type(1-7)ErrorInput.txt contain JSON which has that specific semantic error
implemented within it. Then there are 3 correct text files which contain correct JSON with
no semantic errors. These will be tested using pythons file read within Parser.py, and
outputted to the corresponding output file in 'output_folder'.

Assumptions:
- literals such as false, true, and null, will be expected to be inputted 
  in correct python syntax, which is un-capitalized versions of the word.
- It is assumed that the input contains valid characters and is syntactically correct