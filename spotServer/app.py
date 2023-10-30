from flask import Flask, jsonify, request, make_response
from platforms.aws import AWS
from platforms.gcp import GCP
# from spotServer.platforms.azclient import AZURE
import threading
import string
import random
import db
database = db.DB()

app = Flask(__name__)
# supported_platforms = {"aws": AWS(), "gcp": GCP(), "azure": AZURE()}
supported_platforms = {"aws": AWS(), "gcp": GCP()}

#all platform functions
@app.route('/<string:platform>/create', methods=['POST'])
def create(platform):
    data = request.form
    if platform in list(supported_platforms.keys()):
        taskid = platform+"-"+"".join(random.choices(string.ascii_uppercase+ string.digits, k=5))
        target = threading.Thread(target=supported_platforms[platform].create, args=(data.get("amount"), data.get("keyID"), taskid,))
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
        if platform == "aws":
            for i in database.db.aws.find_one({"APIKeyPair": data.get("apikey")})["Regions"]:
                for ii in database.db.aws.find_one({"APIKeyPair": data.get("apikey")})["Regions"][i]["instances"]:
                    supported_platforms[platform].deleteVM(ii, i)
        if platform == "gcp":
            for i in database.db.gcp.find_one({"APIKeyPair": data.get("apikey")})["Regions"]:
                for ii in database.db.gcp.find_one({"APIKeyPair": data.get("apikey")})["Regions"][i]["instances"]:
                    supported_platforms[platform].deleteVM(ii, i)
        if platform == "azure":
            for i in database.db.azure.find_one({"APIKeyPair": data.get("apikey")})["Regions"]:
                for ii in database.db.azure.find_one({"APIKeyPair": data.get("apikey")})["Regions"][i]["instances"]:
                    supported_platforms[platform].deleteVM(ii, i)
        return make_response('All Instances related to '+data.get("apikey")+" have been terminated")
    else:
        return make_response('platform does not exist', 404)


@app.route('/status/<string:taskid>', methods=['POST'])
def status(taskid):
    if taskid == "all":
        return make_response('Hello world!')
    else:
        return make_response("this task")


@app.route('/<string:platform>/api_key/delete', methods=['POST'])
def deleteAllApiKeyInstances(platform):
    if platform in supported_platforms.keys:
        print(platform)
        return make_response('Hello world!')
    else:
        return make_response('platform does not exist', 404)


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
    
@app.route('/api_key/delete/<string:platform>', methods=['POST'])
def removeApiKey(platform):
    if platform in supported_platforms.keys:
        print(platform)
        return make_response('Hello world!')
    elif platform == "all":
        pass
    else:
        return make_response('platform does not exist', 404)


if __name__ == "__main__":
    # setting debug to True enables hot reload
    # and also provides a debugger shell
    # if you hit an error while running the server
    app.run(debug=True)
