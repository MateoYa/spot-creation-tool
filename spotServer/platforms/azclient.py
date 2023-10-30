# Import the needed credential and management objects from the libraries.
import os, sys
import subprocess
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import db
import sshHandler 
print(
    "Provisioning a virtual machine...some operations might take a \
minute or two."
)
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
RESOURCE_GROUP_NAME = "PythonAzureExample-VM"
LOCATION = "westus2"

# Provision the resource group.
rg_result = resource_client.resource_groups.create_or_update(
    RESOURCE_GROUP_NAME, {"location": LOCATION}
)

print(
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
VNET_NAME = "python-example-vnet5"
SUBNET_NAME = "python-example-subnet"
IP_NAME = "python-example-ip"
IP_CONFIG_NAME = "python-example-ip-config"
NIC_NAME = "python-example-nic"
SECURITY_GROUP_NAME = "ssh-group"
NEW_SECURITY_RULE_NAME = "SSHRULE"
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
print(response.id)
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
    
    {"address_prefix": "10.0.0.0/24",
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

VM_NAME = "ExampleVM"
USERNAME = "azureuser"

print(
    f"Provisioning virtual machine {VM_NAME}; this operation might \
take a few minutes."
)

# Provision the VM specifying only minimal arguments, which defaults
# to an Ubuntu 18.04 VM on a Standard DS1 v2 plan with a public IP address
# and a default virtual network/subnet.
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
with open("./keypairs/"+VM_NAME+'.pem','wb') as pem_out:
    pem_out.write(private_key)
subprocess.run(["chmod", "400", "./keypairs/"+VM_NAME+'.pem'])

adrs = "./keypairs/"+VM_NAME+".pem"
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
                        "key_data": str(public_key.decode())
                    }]
            }        
        }
        }
    }
)

vm_result = poller.result()
print(f"Provisioned virtual machine {vm_result.name}")
sshHandler.configureServer(ip_address_result.ip_address, VM_NAME+'.pem', USERNAME)