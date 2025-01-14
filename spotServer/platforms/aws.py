import math
import subprocess
import time
import os
import boto3
import boto.manage.cmdshell
import datetime

import sys
import os
 
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import db
import sshHandler
class AWS():
    def __init__(self) -> None:    
        self.database = db.DB()
        self.ec2 = boto3.resource('ec2')
        self.currentTASKID = "background prosses"
        self.currentamount = 0
        self.endamount = 1
    def create(self, amount, keyID, taskid):
        self.database.db.taskids.insert_one({"taskid": taskid, "message": "starting"})
        self.taskMessage("starting new instance", localtaskid=taskid, i=0, ii=amount)
        self.StartSpots(amount, ["us-east-1"] ,keyID)
    def CreationStandard(self, SpotAmount, KeyPair):
        return self.ec2.create_instances(
            ImageId='ami-053b0d53c279acc90',
            MinCount=1,
            MaxCount=int(SpotAmount),
            InstanceType='t2.micro',
            KeyName=KeyPair,
            InstanceMarketOptions={
            'MarketType': 'spot',
            'SpotOptions': {
                'MaxPrice': '1',
                'SpotInstanceType': 'one-time',
                'InstanceInterruptionBehavior': 'terminate'
            }}
        )
    #   print(list(x["Regions"].keys()))
        # name = "aws-"+AvailabilityZone[0:-1]+"-"+ KeyPair
        # outfile = open("./keypairs/"+name+'.pem','w')
        # # call the boto ec2 function to create a key pair
        # key_pair = ec2.create_key_pair(KeyName=name)
        # #capture the key and store it in a file
        # KeyPairOut = str(key_pair.key_material)
        # outfile.write(KeyPairOut)
        # subprocess.run(["chmod", "400", "./keypairs/"+name+".pem"])
    # instances = ec2.create_instances(
    #     ImageId='ami-036f5574583e16426',
    #     MinCount=SpotAmount,
    #     MaxCount=SpotAmount,
    #     InstanceType='t2.micro',
    #     KeyName=name
    # )

    # instances = ec2.create_instances(
    #     ImageId='ami-036f5574583e16426',
    #     MinCount=SpotAmount,
    #     MaxCount=SpotAmount,
    #     InstanceType='t2.micro',
    #     KeyName='ec2-keypair',
    #     InstanceMarketOptions={
    #     'MarketType': 'spot',
    #     'SpotOptions': {
    #         'MaxPrice': '1',
    #         'SpotInstanceType': 'one-time'|'persistent',
    #         'BlockDurationMinutes': 123,
    #         'ValidUntil': datetime(2015, 1, 1),
    #         'InstanceInterruptionBehavior': 'terminate'
    #     }
    #     }
    # )
    def BestPrice(self, Region):
        lowest = {"SpotPrice": math.inf}
        for region in Region:
            ec2client = boto3.client('ec2', region_name=region)
            response = ec2client.describe_spot_price_history(
                EndTime=datetime.datetime.today(),
                InstanceTypes=["t2.micro"],
                StartTime=datetime.datetime.today()
            )
            for i in response["SpotPriceHistory"]:
                if float(i["SpotPrice"]) <= float(lowest["SpotPrice"]):
                    lowest = i
        return(lowest)

    def StartSpots(self, SpotAmount, Region, KeyPair):
        AvailabilityZone = self.BestPrice(Region)["AvailabilityZone"]
        Regional = AvailabilityZone[0:-1]
        ec2 = boto3.resource('ec2', region_name=Regional)
        if (KeyPair not in [x["APIKeyPair"] for x in self.database.db.aws.find()]):
            RegionalKeyPair = ec2.create_key_pair(KeyName=KeyPair)
            data = {
                "APIKeyPair": KeyPair,
                "Regions": {
                    Regional: {
                        "KeyPair": str(RegionalKeyPair.key_material),
                        "instances": []
                    }
                }
            }
            self.database.db.aws.insert_one(data)
        elif Regional not in list(self.database.db.aws.find({"APIKeyPair": KeyPair})[0]["Regions"].keys()):
            RegionalKeyPair = ec2.create_key_pair(KeyName=KeyPair)
            self.database.db.aws.update_many({"APIKeyPair": KeyPair},{"$set": {"Regions."+Regional: {"KeyPair": str(RegionalKeyPair.key_material), "instances": []}}})
        self.taskMessage("creating all new instance", i=0)
        ii = 0
        instances = self.CreationStandard(SpotAmount, KeyPair)     
        for instance in instances:
            self.database.db.aws.update_many({"APIKeyPair": KeyPair},{"$push": {"Regions."+Regional+".instances": instance.instance_id}})
            self.taskMessage("waiting for instance to start running", i=ii)
            instance.wait_until_running()
            self.taskMessage("sshing into new instance")
            self.SpotSSH(Regional, KeyPair, instance.instance_id)
            ii += 1
        self.taskMessage("FINISHED", i=ii)
        time.sleep(180)
        self.database.db.taskids.delete_one({"taskid": self.currentTASKID})
    def ApiKeyInstancesRunning(self, KeyPair):
        if (KeyPair in [x["APIKeyPair"] for x in self.database.db.aws.find()]):
            for Region in list(self.database.db.aws.find({"APIKeyPair": KeyPair})[0]["Regions"].keys()):
                ec2_resource = boto3.resource('ec2', region_name=Region)
                for instanceID in self.database.db.aws.find()[0]["Regions"][Region]["instances"]:
                    instance = ec2_resource.Instance(instanceID)
                    if instance.state['Name'] == 'terminated':
                        # Removes Instance From the list
                        instances = self.database.db.aws.find_one({"APIKeyPair": KeyPair})["Regions"][Region]["instances"]
                        instances.remove(instanceID)
                        self.database.db.aws.update_one({"APIKeyPair": KeyPair}, {'$set': {"Regions."+Region+".instances": instances}})
                        # ReAdds Instance to the list
                        instances = self.CreationStandard(1, KeyPair)     
                        for instance in instances:
                            self.database.db.aws.update_many({"APIKeyPair": KeyPair},{"$push": {"Regions."+Region+".instances": instance.instance_id}})
                            instance.wait_until_running()
                            self.SpotSSH(Region, KeyPair, instance.instance_id)
    def SpotSSH(self, Region, KeyPair, InstanceID):
        ec2_client = boto3.client("ec2", region_name=Region)
        print("instance running")
        reservations = ec2_client.describe_instances(InstanceIds=[InstanceID]).get("Reservations")
        for reservation in reservations:
            for instance in reservation['Instances']:
                if instance.get("PublicIpAddress") != None: 
                    print(instance.get("PublicIpAddress"))
                    ip = instance.get("PublicIpAddress").replace(".", "-")
                    host = "ec2-"+ip+".compute-1.amazonaws.com"
                    name = "aws-"+KeyPair
                    with open("./platforms/keypairs/aws.pem",'wb') as pem_out:
                        pem_out.write(str(self.database.db.aws.find_one({"APIKeyPair": KeyPair})["Regions"][Region]["KeyPair"]).encode())
                    adrs = "./keypairs/"+name+".pem"
                    subprocess.run(["chmod", "400", "./platforms/keypairs/aws.pem"])
                    self.taskMessage("waiting for file transfer")
                    time.sleep(25)
                    sshHandler.configureServer(host, "aws.pem", "ubuntu")
                    self.taskMessage("ssh complete")
                    os.remove("./platforms/keypairs/aws.pem")

    def deleteVM(self, vmName, zone):
        self.ec2.instances.filter(InstanceIds=[vmName]).terminate()
        setpass = True
        for i in self.database.db.aws.find():
            if vmName in i["Regions"][zone]["instances"]:
                if setpass:
                    self.database.db.aws.update_many({"APIKeyPair": i["APIKeyPair"]},{"$pull": {"Regions."+zone+".instances": vmName}})
                    setpass = False
    def deleteAPI(self, apikey):
        for i in self.database.db.aws.find_one({"APIKeyPair": apikey})["Regions"]:
            for ii in self.database.db.aws.find_one({"APIKeyPair": apikey})["Regions"][i]["instances"]:
                self.deleteVM(ii, i)
    def taskMessage(self, message, localtaskid="", i=0, ii=0):
        if i != 0:
            self.currentamount = i
        if ii != 0:
            self.endamount = ii
        if localtaskid != "":
            self.currentTASKID = localtaskid

        self.database.db.taskids.update_many({"taskid": self.currentTASKID}, {"$set": {"message": str(self.currentamount)+"/"+str(self.endamount)+" " + message}})
            
# StartSpots(1, ["us-east-1"], "newpair")
# SpotSSH("us-east-1", "newpair", "i-0ca3fa4c880d70e46")
# ApiKeyInstancesRunning("newpair")



# ec2client = boto3.client('ec2')
# keypairs = ec2.describe_key_pairs()
# print(keypairs)
# try:
#     ec2client.delete_key_pair(KeyName='ec2-keypair')
# except Exception as e:
#     print(e)
# # create a file to store the key locally
# outfile = open('ec2-keypair.pem','w')

# # call the boto ec2 function to create a key pair
# key_pair = ec2.create_key_pair(KeyName='ec2-keypair')
# #capture the key and store it in a file
# KeyPairOut = str(key_pair.key_material)
# print(KeyPairOut)
# outfile.write(KeyPairOut)
# subprocess.run(["chmod", "400", "ec2-keypair.pem"])
# # # create a new EC2 instance
# instances = ec2.create_instances(
#      ImageId='ami-036f5574583e16426',
#      MinCount=1,
#      MaxCount=2,
#      InstanceType='t2.micro',
#      KeyName='ec2-keypair'
#  )