# spot-creation-tool
as this tool is meant to be able to work with aws/azure/gcp there are diffrent local credientals you must set up on the device running the spotServer

CHANGE THE SUBSCRIPTION ID ON azclient.py line 28 looks like "self.subscription_id = "**************************"" you must charge the stars

on the mongodb database you can change the port in db.py line 6
must have the following databases: (with this spelling copy and paste is likely best) 
aws
azure
gcp
taskids

aws and gcp settings are fairly intuitive if you want help setting up azure message me

commands for the spot-tool

first off go to the folder ./spot-tool/dist or add the program to the path

commands
./spot-tool setup <URL OF SERVICE>
./spot-tool create <aws/gcp/azure> <number of spot vms> <apikey id>
./spot-tool status all
./spot-tool status <taskID>
./spot-tool terminate instance <aws/gcp/azure> <region> <instanceID>
./spot-tool terminate api <aws/gcp/azure> <apikey>
./spot-tool terminate all
./spot-tool cleanTasks
./spot-tool apikey list


