from flask import Flask, request, make_response
from platforms.aws import AWS
from platforms.gcp import GCP
from platforms.azure import AZURE

app = Flask(__name__)
supported_platforms = {"aws": AWS(), "gcp": GCP(), "azure": AZURE()}


#all platform functions
@app.route('/<string:platform>/create', methods=['POST'])
def create(platform):
    data = request.form
    if platform in list(supported_platforms.keys()):
        return supported_platforms[platform].create(data.get("amount"), data.get("keyID"))
    else:
        return make_response('platform does not exist', 404)

@app.route('/<string:platform>/delete', methods=['POST'])
def delete(platform):
    if platform in supported_platforms.keys:
        print(platform)
        return make_response('Hello world!')
    else:
        return make_response('platform does not exist', 404)

# @app.route('/<string:platform>/api_key/create', methods=['POST'])
# def delete(platform):
#     if platform in supported_platforms.keys:
#         print(platform)
#         return make_response('Hello world!')
#     else:
#         return make_response('platform does not exist', 404)

# @app.route('/<string:platform>/api_key/delete', methods=['POST'])
# def delete(platform):
#     if platform in supported_platforms.keys:
#         print(platform)
#         return make_response('Hello world!')
#     else:
#         return make_response('platform does not exist', 404)

# @app.route('/<string:platform>/api_key/list', methods=['POST'])
# def delete(platform):
#     if platform in supported_platforms.keys:
#         print(platform)
#         return make_response('Hello world!')
#     else:
#         return make_response('platform does not exist', 404)


if __name__ == "__main__":
    # setting debug to True enables hot reload
    # and also provides a debugger shell
    # if you hit an error while running the server
    app.run(debug=True)
