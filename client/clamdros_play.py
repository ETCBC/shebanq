#!/usr/bin/env python
#-*- coding:utf-8 -*-

import clam.common.client
import clam.common.data
import clam.common.status
import random
import sys
import time
import props


#create client, connect to server.#the latter two arguments are required for authenticated webservices,
# they can be omitted otherwise
clamclient = clam.common.client.CLAMClient(props.clamdros_url)#, props.clamdros_username, props.clamdros_password)

#Set a project name (it is recommended to include a sufficiently random naming component here,
# to allow for concurrent uses of the same client)
project = "shebanq" + str(random.getrandbits(64))

#Now we call the webservice and create the project (in this and subsequent methods of clamclient,
# exceptions will be raised on errors).
clamclient.create(project)

#Get project status and specification
data = clamclient.get(project)


#Add one or more input files according to a specific input template.
# The following input templates are defined,each may allow for extra parameters to be specified,
# this is done in the form of Python keyword arguments to the addinputfile() method,
# (parameterid=value)#inputtemplate="mql-query" #MQL Query (PlainTextFormat)#
# The following parameters may be specified for this input template:
#		encoding=...  #(StaticParameter) -   Encoding -  The character encoding of the file
input_filename = "test_files/input/bh_lq01.mql"
output_filename = "test_files/output/bh_lq01-result.xml"
clamclient.addinputfile(project, data.inputtemplate("mql-query"), input_filename)


#Start project execution with custom parameters.
# Parameters are specified as Python keyword arguments to the start() method
# (parameterid=value)#contextlevel=...  #(IntegerParameter) -   Offset -  Limit result context to straw depth
data = clamclient.start(project, contexthandlername="marks", contextlevel=1)


#Always check for parameter errors! Don't just assume everything went well!
# Use startsafe() instead of start#to simply raise exceptions on parameter errors.
if data.errors:
    print >>sys.stderr,"An error occured: " + data.errormsg
    for parametergroup, paramlist in data.parameters:
        for parameter in paramlist:
            if parameter.error:
                print >>sys.stderr,"Error in parameter " + parameter.id + ": " + parameter.error
    clamclient.delete(project) #delete our project (remember, it was temporary, otherwise clients would leave a mess)
    sys.exit(1)

#If everything went well, the system is now running, we simply wait until it is done and retrieve the status
# in the meantime
while data.status != clam.common.status.DONE:
    time.sleep(5) #wait 5 seconds before polling status
    data = clamclient.get(project) #get status again
    print >>sys.stderr, "\tRunning: " + str(data.completion) + '% -- ' + data.statusmessage

print >>sys.stderr, "Finished... " + str(len(data.output)) + " output files"
#Iterate over output files
#for outputfile in data.output:
#
#    # no metadata present!?
#    #try:
#    #outputfile.loadmetadata() #metadata contains information on output template
#
#    #except:
#        #print >>sys.stderr, "exc"
#        #continue
#
#    #outputtemplate = outputfile.metadata.provenance.outputtemplate_id
#    #print outputtemplate
#    #You can check this value against the following predefined output templates,
#    # and determine desired behaviour based on the output template:	#
#    #if outputtemplate == "mql-result": #MQL Query Results (UndefinedXMLFormat)	#Download the remote file
#        #outputfile.copy(output_filename)
#
#    #..or iterate over its (textual) contents one line at a time:
#    #for line in outputfile.readlines():
#		#print line
#
#    print "\tFILE: " + str(outputfile)
#    print "\tCONTENTS: "
#    #Download and immediately read the output file
#    for line in outputfile:
#        print "\t\t" + line,
#    print


print(len(data.output[0].readlines()))

for line in data.output[0]:
    print(line)

zipurl = data.baseurl + "/" + project + "/output/zip/"
print("zip url: " + zipurl)

#zipfile = open(project+".zip", "w")
#clamclient.downloadarchive(project, zipfile)
#zipfile.close()


#delete the project (otherwise it would remain on server and clients would leave a mess)
clamclient.delete(project)
