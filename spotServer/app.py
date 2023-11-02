import time
from flask import Flask, jsonify, request, make_response
from platforms.aws import AWS
from platforms.gcp import GCP
from platforms.azclient import AZURE
import threading
import string
import random
import db
database = db.DB()

app = Flask(__name__)
supported_platforms = {"aws": AWS(), "gcp": GCP(), "azure": AZURE()}
# supported_platforms = {"aws": AWS(), "gcp": GCP()}

database.db.taskids.delete_many({})

#all platform functions
@app.route('/<string:platform>/create', methods=['POST'])
def create(platform):
    data = request.form
    if platform in list(supported_platforms.keys()):
        taskid = platform+"-"+"".join(random.choices(string.ascii_uppercase+ string.digits, k=5))
        target = threading.Thread(target=supported_platforms[platform].create, args=(data.get("amount"), data.get("apikey"), taskid,))
        target.start()
        # return supported_platforms[platform].create(data.get("amount"), data.get("keyID"))
        return taskid
    else:
        return make_response('platform does not exist', 404)

@app.route('/<string:platform>/delete', methods=['POST'])
def deleteInstance(platform):
    data = request.form
    if platform in list(supported_platforms.keys()):
        target = threading.Thread(target=supported_platforms[platform].deleteVM, args=(data.get("instance"), data.get("zone"),))
        target.start()
       
        return make_response('Deleted '+data.get("instance"))
    else:
        return make_response('platform does not exist', 404)

@app.route('/<string:platform>/delete/api', methods=['POST'])
def deleteAPIKEYinstances(platform):
    data = request.form
    if platform in list(supported_platforms.keys()):
        target = threading.Thread(target=supported_platforms[platform].deleteAPI, args=(data.get("apikey"),))
        target.start()
        return make_response('All Instances related to '+data.get("apikey")+" have been terminated")
    else:
        return make_response('platform does not exist', 404)
@app.route('/delete/all', methods=['GET'])
def deleteAllAPIKEYinstances():
    instances = {}
    for i in database.db.aws.find():
        target = threading.Thread(target=supported_platforms["aws"].deleteAPI, args=(i["APIKeyPair"],))
        target.start()
    for i in database.db.gcp.find():
        target = threading.Thread(target=supported_platforms["gcp"].deleteAPI, args=(i["APIKeyPair"],))
        target.start()
    for i in database.db.azure.find():
        target = threading.Thread(target=supported_platforms["azure"].deleteAPI, args=(i["APIKeyPair"],))
        target.start()
    return make_response("All Instances have been terminated")



@app.route('/status/<string:taskid>', methods=['GET'])
def status(taskid):
    if taskid == "all":
        instances = {}
        aws = {}
        for i in database.db.aws.find():
            keypair = {}
            for ii in list(i["Regions"].keys()):
                try:
                    keypair[ii] += i["Regions"][ii]["instances"]
                except Exception:
                    keypair[ii] = i["Regions"][ii]["instances"]
            aws[i["APIKeyPair"]] = keypair
        gcp = {}
        for i in database.db.gcp.find():
            keypair = {}
            for ii in list(i["Regions"].keys()):
                try:
                    keypair[ii] += i["Regions"][ii]["instances"]
                except Exception:
                    keypair[ii] = i["Regions"][ii]["instances"]
            gcp[i["APIKeyPair"]] = keypair
        azure = {}
        for i in database.db.azure.find():
            keypair = {}
            for ii in list(i["Regions"].keys()):
                try:
                    keypair[ii] += i["Regions"][ii]["instances"]
                except Exception:
                    keypair[ii] = i["Regions"][ii]["instances"]
            azure[i["APIKeyPair"]] = keypair
        tasks = {}
        for i in database.db.taskids.find():
            tasks[i["taskid"]] = i["message"]
        instances["aws"] = aws
        instances["gcp"] = gcp
        instances["azure"] = azure
        instances["tasks"] = tasks
        return jsonify(instances)
    else:
        return make_response(database.db.taskids.find({"taskid": taskid})[0]["message"])

# done
@app.route('/api_key/list', methods=['GET'])
def apiKeyList():
    aws = []
    for doc in database.db.aws.find():
        aws.append(doc["APIKeyPair"])
    gcp = []
    for doc in database.db.gcp.find():
        gcp.append(doc["APIKeyPair"])
    azure = []
    for doc in database.db.azure.find():
        azure.append(doc["APIKeyPair"])
    data = {"aws": aws, "gcp": gcp, "azure": azure}
    return jsonify(data)

@app.route('/cleartasks', methods=['GET'])
def cleartasks():
    database.db.taskids.delete_many({})
    return make_response('all tasks cleared')

def maintain():
    while True:
        for i in database.db.aws.find():
            supported_platforms["aws"].ApiKeyInstancesRunning(i["APIKeyPair"])
        for i in database.db.gcp.find():
                    supported_platforms["aws"].ApiKeyInstancesRunning(i["APIKeyPair"])
        for i in database.db.azure.find():
            supported_platforms["aws"].ApiKeyInstancesRunning(i["APIKeyPair"])
        print("hi")
        time.sleep(300)

target = threading.Thread(target=maintain)
target.start()

if __name__ == "__main__":
    # setting debug to True enables hot reload
    # and also provides a debugger shell
    # if you hit an error while running the server
    app.run(debug=True)
