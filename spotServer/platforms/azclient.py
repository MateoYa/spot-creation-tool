# Import the needed credential and management objects from the libraries.
import os, sys
import string
from typing import Dict, Iterable
import random
import subprocess
import time
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.compute.models import VirtualMachinePriorityTypes, VirtualMachineEvictionPolicyTypes, BillingProfile
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import db
import sshHandler 

class AZURE():
    def __init__(self) -> None:
        self.ZONE = "westus2"
        self.database = db.DB()
        self.credential = AzureCliCredential()
        self.subscription_id = "**********************"
        self.currentamount = 0
        self.endamount = 1
        self.currentTASKID = ""
    def create(self, amount, keyID, taskid):
        self.database.db.taskids.insert_one({"taskid": taskid, "message": "starting"})
        self.taskMessage("starting up", localtaskid=taskid, ii=amount)
        if (keyID not in [x["APIKeyPair"] for x in self.database.db.azure.find()]):
            key = rsa.generate_private_key(
            backend=crypto_default_backend(),
            public_exponent=65537,
            key_size=2048
            )
            private_key = key.private_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PrivateFormat.TraditionalOpenSSL,
                crypto_serialization.NoEncryption()
            )
            public_key = key.public_key().public_bytes(
                crypto_serialization.Encoding.OpenSSH,
                crypto_serialization.PublicFormat.OpenSSH
            )
            data = {
                    "APIKeyPair": keyID,
                    "Regions": {
                        self.ZONE: {
                            "resource_group_name": self.ZONE+"-groupname",
                            "PrivateKeyPair": str(private_key.decode()),
                            "PublicKeyPair": str(public_key.decode()),
                            "instances": []
                        }
                    }
            }
            self.database.db.azure.insert_one(data)
        for i in range(int(amount)):
            self.taskMessage("Creating VM", i=i)
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            vm_list = compute_client.virtual_machines.list_all()
            vms = {}
            for vm in vm_list:
                try:
                    vms[vm.location] += 1
                except Exception as e:
                    vms[vm.location] = 1
            if self.ZONE in list(vms.keys()):
                if vms[self.ZONE] >= 2:
                    client = SubscriptionClient(self.credential)
                    response = client.subscriptions.list_locations(subscription_id=self.subscription_id)
                    newLocationFinding = True
                    locations = ["australiacentral","australiaeast","australiasoutheast","brazilsouth","canadacentral","canadaeast","centralindia","centralus","eastasia","eastus2","eastus","francecentral","germanywestcentral","japaneast","japanwest","jioindiawest","koreacentral","koreasouth","northcentralus","northeurope","norwayeast","southafricanorth","southcentralus","southindia","southeastasia","swedencentral","switzerlandnorth","uaenorth","westcentralus","westeurope","westindia","westus2","westus3","westus","polandcentral","qatarcentral","australiacentral2","israelcentral","italynorth","centraluseuap","eastus2euap","eastusstg","southcentralusstg"]
                    while newLocationFinding:
                        i = random.randint(0, len(locations)-1)
                        if locations[i] not in list(vms.keys()):
                            self.ZONE = locations[i] 
                            newLocationFinding = False
                        elif vms[locations[i]] >= 2:
                            self.ZONE = locations[i] 
                            newLocationFinding = False
                        key = rsa.generate_private_key(
                        backend=crypto_default_backend(),
                        public_exponent=65537,
                        key_size=2048
                        )
                        private_key = key.private_bytes(
                            crypto_serialization.Encoding.PEM,
                            crypto_serialization.PrivateFormat.TraditionalOpenSSL,
                            crypto_serialization.NoEncryption()
                        )
                        public_key = key.public_key().public_bytes(
                            crypto_serialization.Encoding.OpenSSH,
                            crypto_serialization.PublicFormat.OpenSSH
                        )
                        data = {
                                "resource_group_name": self.ZONE+"-groupname",
                                "PrivateKeyPair": str(private_key.decode()),
                                "PublicKeyPair": str(public_key.decode()),
                                "instances": []
                        }
                        self.database.db.azure.update_many({"APIKeyPair": keyID},{"$set": {"Regions."+self.ZONE: data}})

            instanceNAME = "".join(random.choices(string.ascii_lowercase, k=10))
            ip, vmNAME = self.create_instance(instanceNAME, self.ZONE, key=keyID)
            self.database.db.azure.update_many({"APIKeyPair": keyID},{"$push": {"Regions."+self.ZONE+".instances": vmNAME}})
            
            try:
                os.remove("./platforms/keypairs/azure.pem")
            except Exception:
                pass
            with open("./platforms/keypairs/azure.pem",'wb') as pem_out:
                pem_out.write(str(self.database.db.azure.find_one({"APIKeyPair": keyID})["Regions"][self.ZONE]["PrivateKeyPair"]).encode())
            subprocess.run(["chmod", "400", "./platforms/keypairs/azure.pem"])
            self.taskMessage("wating to ssh into the server")
            time.sleep(30)
            self.taskMessage("sshing into the server")
            sshHandler.configureServer(ip, "azure.pem", "azureuser")
            os.remove("./platforms/keypairs/azure.pem")
        self.taskMessage("FINSIHED", i=amount)
        self.database.db.taskids.delete_one({"taskid": self.currentTASKID})
    def taskMessage(self, message, localtaskid="", i=0, ii=0):
        if i != 0:
            self.currentamount = i
        if ii != 0:
            self.endamount = ii
        if localtaskid != "":
            self.currentTASKID = localtaskid

        self.database.db.taskids.update_many({"taskid": self.currentTASKID}, {"$set": {"message": str(self.currentamount)+"/"+str(self.endamount)+" " + message}})
    def deleteVM(self, vmName, zone):
        setpass = True
        for i in self.database.db.azure.find():
            print(i["Regions"][zone]["instances"])
            if vmName in i["Regions"][zone]["instances"]:
                if setpass:
                    self.database.db.azure.update_many({"APIKeyPair": i["APIKeyPair"]},{"$pull": {"Regions."+zone+".instances": vmName}})
                    local_resource_group_name =i["Regions"][zone]["resource_group_name"]
                    setpass = False
        client = ComputeManagementClient(self.credential, self.subscription_id)
        client.virtual_machines.begin_delete(local_resource_group_name, vmName, ).wait()
        client = NetworkManagementClient(self.credential, self.subscription_id)
        
        client.network_interfaces.begin_delete(resource_group_name=local_resource_group_name, network_interface_name=vmName+"-nic").wait()
        client.public_ip_addresses.begin_delete(resource_group_name=local_resource_group_name, public_ip_address_name=vmName+"-ip").wait()
        client.subnets.begin_delete(resource_group_name=local_resource_group_name, virtual_network_name=vmName+"-net", subnet_name=vmName+"-subnet").wait() 
        client.virtual_networks.begin_delete(
        resource_group_name=local_resource_group_name,
        virtual_network_name= vmName+"-net",).wait()   
        client = ComputeManagementClient(self.credential, self.subscription_id)
        disks_list = client.disks.list_by_resource_group(local_resource_group_name)
        for disk in disks_list:
            if vmName in disk.name:
                client.disks.begin_delete(local_resource_group_name, disk.name).wait()
    def deleteAPI(self, apikey):
        for i in self.database.db.azure.find_one({"APIKeyPair": apikey})["Regions"]:
            for ii in self.database.db.azure.find_one({"APIKeyPair": apikey})["Regions"][i]["instances"]:
                self.deleteVM(ii, i)
    def ApiKeyInstancesRunning(self, apikey):
        compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        vm_list = compute_client.virtual_machines.list_all()
        vm_names = []
        for vm in vm_list:
            vm_names.append(vm.name)
        for i in self.database.db.azure.find_one({"APIKeyPair": apikey})["Regions"]:
            for ii in self.database.db.azure.find_one({"APIKeyPair": apikey})["Regions"][i]["instances"]:
                if ii not in vm_names:
                    ip, vmNAME = self.create_instance(ii, i, apikey)
                    try:
                        os.remove("./platforms/keypairs/azure.pem")
                    except Exception:
                        pass
                    with open("./platforms/keypairs/azure.pem",'wb') as pem_out:
                        pem_out.write(str(self.database.db.azure.find_one({"APIKeyPair": apikey})["Regions"][i]["PrivateKeyPair"]).encode())
                    subprocess.run(["chmod", "400", "./platforms/keypairs/azure.pem"])
                    time.sleep(30)
                    sshHandler.configureServer(ip, "azure.pem", "azureuser")
                    os.remove("./platforms/keypairs/azure.pem")

    def create_instance(self, VM_NAME, LOCATION, key):
        self.taskMessage("starting to create "+VM_NAME)
        # Acquire a credential object using CLI-based authentication.
        credential = AzureCliCredential()

        # Retrieve subscription ID from environment variable.
        subscription_id = "6f15e407-5316-4a46-8972-d9a2d63cc29d"


        # Step 1: Provision a resource group

        # Obtain the management object for resources, using the credentials
        # from the CLI login.
        resource_client = ResourceManagementClient(credential, subscription_id)

        # Constants we need in multiple places: the resource group name and
        # the region in which we provision resources. You can change these
        # values however you want.
        RESOURCE_GROUP_NAME = self.database.db.azure.find({"APIKeyPair": key})[0]["Regions"][LOCATION]["resource_group_name"]

        # Provision the resource group.
        rg_result = resource_client.resource_groups.create_or_update(
            RESOURCE_GROUP_NAME, {"location": LOCATION}
        )

        self.taskMessage(
            f"Provisioned resource group {rg_result.name} in the \
        {rg_result.location} region"
        )

        # For details on the previous code, see Example: Provision a resource
        # group at https://learn.microsoft.com/azure/developer/python/
        # azure-sdk-example-resource-group

        # Step 2: provision a virtual network

        # A virtual machine requires a network interface client (NIC). A NIC
        # requires a virtual network and subnet along with an IP address.
        # Therefore we must provision these downstream components first, then
        # provision the NIC, after which we can provision the VM.

        # Network and IP address names
        VNET_NAME = VM_NAME+"-net"
        SUBNET_NAME = VM_NAME+"-subnet"
        IP_NAME = VM_NAME+"-ip"
        IP_CONFIG_NAME = VM_NAME+"-ip-config"
        NIC_NAME = VM_NAME+"-nic"
        SECURITY_GROUP_NAME = "ssh-group"
        # Obtain the management object for networks
        network_client = NetworkManagementClient(credential, subscription_id)

        # Provision the virtual network and wait for completion
        try:
            poller = network_client.virtual_networks.get(RESOURCE_GROUP_NAME, VNET_NAME)
        except Exception as e:
            
            poller = network_client.virtual_networks.begin_create_or_update(
                RESOURCE_GROUP_NAME,
                VNET_NAME,
                {
                    "location": LOCATION,
                    "address_space": {"address_prefixes": ["10.0.0.0/16"]},
                },
            )

            vnet_result = poller.result()

            print(
                f"Provisioned virtual network {vnet_result.name} with address \
            prefixes {vnet_result.address_space.address_prefixes}"
            )

        response = network_client.network_security_groups.begin_create_or_update(
            resource_group_name=RESOURCE_GROUP_NAME,
            network_security_group_name=SECURITY_GROUP_NAME,
            parameters={"location": LOCATION},
        ).result()
        async_security_rule = network_client.security_rules.begin_create_or_update(
            RESOURCE_GROUP_NAME,
            SECURITY_GROUP_NAME,
            "rule1",
                security_rule_parameters={
                    "properties": {
                        "access": "Allow",
                        "destinationAddressPrefix": "*",
                        "destinationPortRange": "22",
                        "direction": "Inbound",
                        "priority": 100,
                        "protocol": "tcp",
                        "sourceAddressPrefix": "*",
                        "sourcePortRange": "*",
                    }
                },
        )
        # Step 3: Provision the subnet and wait for completion
        poller = network_client.subnets.begin_create_or_update(
            RESOURCE_GROUP_NAME,
            VNET_NAME,
            SUBNET_NAME,
            
            {"address_prefix": "10.0."+str(random.randint(1,254))+".0/24",
            "networkSecurityGroup": {
                    "id": response.id,
                    "location": LOCATION
            }
            }
        )
        subnet_result = poller.result()

        print(
            f"Provisioned virtual subnet {subnet_result.name} with address \
        prefix {subnet_result.address_prefix}"
        )

        # Step 4: Provision an IP address and wait for completion
        poller = network_client.public_ip_addresses.begin_create_or_update(
            RESOURCE_GROUP_NAME,
            IP_NAME,
            {
                "location": LOCATION,
                "sku": {"name": "Standard"},
                "public_ip_allocation_method": "Static",
                "public_ip_address_version": "IPV4",
            },
        )

        ip_address_result = poller.result()

        print(
            f"Provisioned public IP address {ip_address_result.name} \
        with address {ip_address_result.ip_address}"
        )

        # Step 5: Provision the network interface client
        poller = network_client.network_interfaces.begin_create_or_update(
            RESOURCE_GROUP_NAME,
            NIC_NAME,
            {
                "location": LOCATION,
                "ip_configurations": [
                    {
                        "name": IP_CONFIG_NAME,
                        "subnet": {"id": subnet_result.id},
                        "public_ip_address": {"id": ip_address_result.id},
                    }
                ],
            },
        )

        nic_result = poller.result()
        print(f"Provisioned network interface client {nic_result.name}")
        # Step 6: Provision the virtual machine

        # Obtain the management object for virtual machines
        compute_client = ComputeManagementClient(credential, subscription_id)

        USERNAME = "azureuser"

        print(
            f"Provisioning virtual machine {VM_NAME}; this operation might \
        take a few minutes."
        )

        # Provision the VM specifying only minimal arguments, which defaults
        # to an Ubuntu 18.04 VM on a Standard DS1 v2 plan with a public IP address
        # and a default virtual network/subnet.
        adrs = "./keypairs/"+VM_NAME+".pem"
        self.taskMessage("Creating VM")
        poller = compute_client.virtual_machines.begin_create_or_update(
            RESOURCE_GROUP_NAME,
            VM_NAME,
            {
                "location": LOCATION,
                "storage_profile": {
                    "image_reference": {
                        "publisher": "Canonical",
                        "offer": "UbuntuServer",
                        "sku": "16.04.0-LTS",
                        "version": "latest",
                    }
                },
                "hardware_profile": {"vm_size": "Standard_B2ats_v2"},
                "network_profile": {
                    "network_interfaces": [
                        {
                            "id": nic_result.id,
                        }
                    ]
                },
                "os_profile": {
                    "computer_name": VM_NAME,
                    "admin_username": USERNAME,
                    "linux_configuration": {
                        "disable_password_authentication": True,
                        "ssh": {
                            "public_keys": [{
                                "path": "/home/{}/.ssh/authorized_keys".format(USERNAME),
                                "key_data": self.database.db.azure.find_one({"APIKeyPair": key})["Regions"][self.ZONE]["PublicKeyPair"]
                            }]
                    }        
                }
                },
                'priority':VirtualMachinePriorityTypes.spot, # use Azure spot intance
                'eviction_policy':VirtualMachineEvictionPolicyTypes.deallocate , #For Azure Spot virtual machines, the only supported value is 'Deallocate'
                'billing_profile': BillingProfile(max_price=float(2)) 
            }
        )

        vm_result = poller.result()
        print(f"Provisioned virtual machine {vm_result.name}")
        return ip_address_result.ip_address, VM_NAME