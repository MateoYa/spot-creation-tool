import click
import requests
import json

url = "http://127.0.0.1:5000/"
# Opening JSON file
with open('../config.json', 'r') as openfile:
    json_object = json.load(openfile)
    if json_object["url"] != "":
        url = json_object["url"] 
@click.group()
def groupcli():
    pass

@groupcli.command()
@click.argument(
    "args",
    nargs=-1
)
def setup(args):
    with open("../config.json", "w") as o:
        data = {"url": args[0]}
        json_object = json.dumps(data, indent=4)
        o.write(json_object)
        o.close()
    print("set target to: "+ args[0])

@groupcli.command()
@click.argument(
    "args",
    nargs=-1
)
def create(args):
    platform = args[0]
    amount = args[1]
    keyid = args[2]
    myobj = {'amount': amount, "apikey": keyid}
    rsp = requests.post(url+platform+"/create", myobj)
    print(rsp.text)


# spot-tool status <taskID/all>
@groupcli.command()
@click.argument(
    "args",
    nargs=-1
)
def status(args):
    taskid = args[0]
    rsp = requests.get(url+"/status/"+taskid).json()
    json_object = json.dumps(rsp, indent=4)
    print(json_object)

# spot-tool terminate <gcp> 
@groupcli.command()
@click.argument(
    "args",
    nargs=-1
)
def terminate(args):
    state = args[0]
    if state == "instance":
        platform = args[1]
        region = args[2]
        instance = args[3]
        myobj = {'instance': instance, "zone": region}
        rsp = requests.post(url+platform+"/delete", myobj)
        print(rsp.text)
    if state == "api":
        platform = args[1]
        apikey = args[2]
        myobj = {'apikey': apikey}
        rsp = requests.post(url+platform+"/delete/api", myobj)
        print(rsp.text)
    if state == "all":
        rsp = requests.get(url+"/delete/all")
        print(rsp.text)

@groupcli.command()
@click.argument(
    "args",
    nargs=-1
)
def cleanTasks(args):
    rsp = requests.get(url+"cleartasks")
    print(rsp.text)

@groupcli.command()
@click.argument(
    "args",
    nargs=-1
)
def apikey(args):
    if args[0] == "list":
        rsp = requests.get(url+"/api_key/list").json()
        json_object = json.dumps(rsp, indent=4)
        print(json_object)


if __name__ == '__main__':
    groupcli()