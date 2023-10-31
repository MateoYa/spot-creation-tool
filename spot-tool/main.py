import click
import requests

url = "http://127.0.0.1:5000/"

@click.group()
def groupcli():
    pass

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
    rsp = requests.get(url+"/status/"+taskid)
    print(rsp.text)

if __name__ == '__main__':
    groupcli()