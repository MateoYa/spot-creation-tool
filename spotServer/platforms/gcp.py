from __future__ import annotations
import random
import re
import string
import subprocess
import sys
from typing import Any, Dict, Iterable
import warnings
from google.protobuf.json_format import MessageToJson
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
import googleapiclient.discovery
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import os
import time
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import db
import sshHandler
datebase = db.DB()

class GCP():
    def __init__(self) -> None:
        self.database = db.DB()
        self.project_ID = "testing-vm-with-api"
        self.ZONE = "us-west1-a"
        self.currentTASKID = "background prosses"
        self.currentamount = 0
        self.endamount = 1
    def create(self, amount, keyID, taskid):
        self.database.db.taskids.insert_one({"taskid": taskid, "message": "starting"})
        self.ZONE = "us-west1-a"
        if (keyID not in [x["APIKeyPair"] for x in self.database.db.gcp.find()]):
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
                            "PrivateKeyPair": str(private_key.decode()),
                            "PublicKeyPair": str(public_key.decode()),
                            "instances": []
                        }
                    }
            }
            self.database.db.gcp.insert_one(data)

        for i in range(int(amount)):
            self.taskMessage("starting new instance", localtaskid=taskid, i=i, ii=amount)
            if(len(self.list_all_instances(self.project_ID, self.ZONE)) >= 7):
                newLocationFinding = True
                locations = ["us-west1-a", "us-west2-a", "us-west3-a","us-west4-a", "us-south1-a", "us-east1-a","us-east4-b", "us-east5-a", "us-central-a"]
                while newLocationFinding:
                    ii = random.randint(0, len(locations)-1)
                    if(len(self.list_all_instances(self.project_ID, locations[ii])) <= 7):
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
                        "PrivateKeyPair": str(private_key.decode()),
                        "PublicKeyPair": str(public_key.decode()),
                        "instances": []
                }
                self.database.db.gcp.update_many({"APIKeyPair": keyID},{"$set": {"Regions."+self.ZONE: data}})
            instanceNAME = "".join(random.choices(string.ascii_lowercase, k=10))
            instance = self.create_instance(project_id=self.project_ID, zone=self.ZONE, instance_name=instanceNAME, key=keyID, spot=True, external_access=True)
            self.database.db.gcp.update_many({"APIKeyPair": keyID},{"$push": {"Regions."+self.ZONE+".instances": instance.name}})
            
            host = str(instance.network_interfaces[0].access_configs[0].nat_i_p)
            try:
                os.remove("./platforms/keypairs/gcp.pem")
            except Exception:
                pass
            with open("./platforms/keypairs/gcp.pem",'wb') as pem_out:
                pem_out.write(str(self.database.db.gcp.find_one({"APIKeyPair": keyID})["Regions"][self.ZONE]["PrivateKeyPair"]).encode())
            subprocess.run(["chmod", "400", "./platforms/keypairs/gcp.pem"])
            self.taskMessage("waiting for ssh")
            time.sleep(25)
            self.taskMessage("sshing into server")
            sshHandler.configureServer(host, "gcp.pem", "spotcontroller")
            os.remove("./platforms/keypairs/gcp.pem")
        self.taskMessage("FINISHED", i=amount)
        time.sleep(180)
        self.database.db.taskids.delete_one({"taskid": self.currentTASKID})

    def taskMessage(self, message, localtaskid="", i=0, ii=0):
        if i != 0:
            self.currentamount = i
        if ii != 0:
            self.endamount = ii
        if localtaskid != "":
            self.currentTASKID = localtaskid

        self.database.db.taskids.update_many({"taskid": self.currentTASKID}, {"$set": {"message": str(self.currentamount)+"/"+str(self.endamount)+" " + message}})
    def list_all_instances(
        self,
        project_id: str,
        region: str
    ) -> Dict[str, Iterable[compute_v1.Instance]]:

        instance_client = compute_v1.InstancesClient()
        request = {
                "project" : project_id,
                }

        agg_list = instance_client.aggregated_list(request=request)

        all_instances = {}
        print("Instances found:")
        i = []
        for zone, response in agg_list:
            if response.instances:
                if re.search(f"{region}*", zone):
                    all_instances[zone] = response.instances
                    print(f" {zone}:")
                    for instance in response.instances:
                        i.append(instance.name)
                        print(f" - {instance.name} ({instance.machine_type})")
        return i
    def deleteVM(self, vmName, zone):
        setpass = True
        for i in self.database.db.gcp.find():
            try:
                if vmName in i["Regions"][zone]["instances"]:
                    if setpass:
                        self.database.db.gcp.update_many({"APIKeyPair": i["APIKeyPair"]},{"$pull": {"Regions."+zone+".instances": vmName}})
                        setpass = False
            except Exception:
                pass
        instance_client = compute_v1.InstancesClient()
        instance_client.delete(project=self.project_ID,zone=zone,instance=vmName)
    def ApiKeyInstancesRunning(self, apikey):
        for i in self.database.db.gcp.find_one({"APIKeyPair": apikey})["Regions"]:
            vm_names = self.list_all_instances(self.project_ID, i)
            for ii in self.database.db.gcp.find_one({"APIKeyPair": apikey})["Regions"][i]["instances"]:
                if ii not in vm_names:
                    instance = self.create_instance(project_id=self.project_ID, zone=i, instance_name=ii, key=apikey, spot=True,external_access=True)
                    host = str(instance.network_interfaces[0].access_configs[0].nat_i_p)
                    try:
                        os.remove("./platforms/keypairs/gcp.pem")
                    except Exception:
                        pass
                    with open("./platforms/keypairs/gcp.pem",'wb') as pem_out:
                        pem_out.write(str(self.database.db.gcp.find_one({"APIKeyPair": apikey})["Regions"][i]["PrivateKeyPair"]).encode())
                    subprocess.run(["chmod", "400", "./platforms/keypairs/gcp.pem"])
                    time.sleep(25)
                    sshHandler.configureServer(host, "gcp.pem", "spotcontroller")
                    os.remove("./platforms/keypairs/gcp.pem")
    def deleteAPI(self, apikey):
        for i in self.database.db.gcp.find_one({"APIKeyPair": apikey})["Regions"]:
            for ii in self.database.db.gcp.find_one({"APIKeyPair": apikey})["Regions"][i]["instances"]:
                self.deleteVM(ii, i)

    def disk_from_image(
        self,
        disk_type: str,
        disk_size_gb: int,
        boot: bool,
        source_image: str,
        auto_delete: bool = True,
    ) -> compute_v1.AttachedDisk:
        """
        Create an AttachedDisk object to be used in VM instance creation. Uses an image as the
        source for the new disk.

        Args:
            disk_type: the type of disk you want to create. This value uses the following format:
                "zones/{zone}/diskTypes/(pd-standard|pd-ssd|pd-balanced|pd-extreme)".
                For example: "zones/us-west3-b/diskTypes/pd-ssd"
            disk_size_gb: size of the new disk in gigabytes
            boot: boolean flag indicating whether this disk should be used as a boot disk of an instance
            source_image: source image to use when creating this disk. You must have read access to this disk. This can be one
                of the publicly available images or an image from one of your projects.
                This value uses the following format: "projects/{project_name}/global/images/{image_name}"
            auto_delete: boolean flag indicating whether this disk should be deleted with the VM that uses it

        Returns:
            AttachedDisk object configured to be created using the specified image.
        """
        boot_disk = compute_v1.AttachedDisk()
        initialize_params = compute_v1.AttachedDiskInitializeParams()
        initialize_params.source_image = source_image
        initialize_params.disk_size_gb = disk_size_gb
        initialize_params.disk_type = disk_type
        boot_disk.initialize_params = initialize_params
        # Remember to set auto_delete to True if you want the disk to be deleted when you delete
        # your VM instance.
        boot_disk.auto_delete = auto_delete
        boot_disk.boot = boot
        return boot_disk
    def wait_for_extended_operation(
        self, operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
    ) -> Any:
        """
        Waits for the extended (long-running) operation to complete.

        If the operation is successful, it will return its result.
        If the operation ends with an error, an exception will be raised.
        If there were any warnings during the execution of the operation
        they will be printed to sys.stderr.

        Args:
            operation: a long-running operation you want to wait on.
            verbose_name: (optional) a more verbose name of the operation,
                used only during error and warning reporting.
            timeout: how long (in seconds) to wait for operation to finish.
                If None, wait indefinitely.

        Returns:
            Whatever the operation.result() returns.

        Raises:
            This method will raise the exception received from `operation.exception()`
            or RuntimeError if there is no exception set, but there is an `error_code`
            set for the `operation`.

            In case of an operation taking longer than `timeout` seconds to complete,
            a `concurrent.futures.TimeoutError` will be raised.
        """
        result = operation.result(timeout=timeout)

        if operation.error_code:
            print(
                f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
                file=sys.stderr,
                flush=True,
            )
            print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
            raise operation.exception() or RuntimeError(operation.error_message)

        if operation.warnings:
            print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
            for warning in operation.warnings:
                print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

        return result
    def create_instance(
        self,
        project_id: str,
        zone: str,
        instance_name: str,
        key: str,
        # disks: list[compute_v1.AttachedDisk],
        machine_type: str = "e2-micro",
        network_link: str = "global/networks/default",
        subnetwork_link: str = None,
        internal_ip: str = None,
        external_access: bool = False,
        external_ipv4: str = None,
        accelerators: list[compute_v1.AcceleratorConfig] = None,
        preemptible: bool = False,
        spot: bool = False,
        instance_termination_action: str = "DELETE",
        custom_hostname: str = None,
        delete_protection: bool = False,
    ) -> compute_v1.Instance:
        """
        Send an instance creation request to the Compute Engine API and wait for it to complete.

        Args:
            project_id: project ID or project number of the Cloud project you want to use.
            zone: name of the zone to create the instance in. For example: "us-west3-b"
            instance_name: name of the new virtual machine (VM) instance.
            disks: a list of compute_v1.AttachedDisk objects describing the disks
                you want to attach to your new instance.
            machine_type: machine type of the VM being created. This value uses the
                following format: "zones/{zone}/machineTypes/{type_name}".
                For example: "zones/europe-west3-c/machineTypes/f1-micro"
            network_link: name of the network you want the new instance to use.
                For example: "global/networks/default" represents the network
                named "default", which is created automatically for each project.
            subnetwork_link: name of the subnetwork you want the new instance to use.
                This value uses the following format:
                "regions/{region}/subnetworks/{subnetwork_name}"
            internal_ip: internal IP address you want to assign to the new instance.
                By default, a free address from the pool of available internal IP addresses of
                used subnet will be used.
            external_access: boolean flag indicating if the instance should have an external IPv4
                address assigned.
            external_ipv4: external IPv4 address to be assigned to this instance. If you specify
                an external IP address, it must live in the same region as the zone of the instance.
                This setting requires `external_access` to be set to True to work.
            accelerators: a list of AcceleratorConfig objects describing the accelerators that will
                be attached to the new instance.
            preemptible: boolean value indicating if the new instance should be preemptible
                or not. Preemptible VMs have been deprecated and you should now use Spot VMs.
            spot: boolean value indicating if the new instance should be a Spot VM or not.
            instance_termination_action: What action should be taken once a Spot VM is terminated.
                Possible values: "STOP", "DELETE"
            custom_hostname: Custom hostname of the new VM instance.
                Custom hostnames must conform to RFC 1035 requirements for valid hostnames.
            delete_protection: boolean value indicating if the new virtual machine should be
                protected against deletion or not.
        Returns:
            Instance object.
        """
        instance_client = compute_v1.InstancesClient()

        # Use the network interface provided in the network_link argument.
        network_interface = compute_v1.NetworkInterface()
        network_interface.network = network_link
        if subnetwork_link:
            network_interface.subnetwork = subnetwork_link

        if internal_ip:
            network_interface.network_i_p = internal_ip

        if external_access:
            access = compute_v1.AccessConfig()
            access.type_ = compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT.name
            access.name = "External NAT"
            access.network_tier = access.NetworkTier.PREMIUM.name
            if external_ipv4:
                access.nat_i_p = external_ipv4
            network_interface.access_configs = [access]

        # Collect information into the Instance object.
        instance = compute_v1.Instance()
        instance.network_interfaces = [network_interface]
        instance.name = instance_name
        new_disk = compute_v1.AttachedDisk()
        new_disk.initialize_params.disk_size_gb = 10
        new_disk.initialize_params.source_image = "projects/debian-cloud/global/images/debian-11-bullseye-v20231010"
        new_disk.auto_delete = True
        new_disk.boot = True
        new_disk.type_ = "PERSISTENT"
        instance.disks.append(new_disk)
        instance.metadata.items.append({"key": "ssh-keys", "value": "spotcontroller:"+self.database.db.gcp.find_one({"APIKeyPair": key})["Regions"][self.ZONE]["PublicKeyPair"]})

        if re.match(r"^zones/[a-z\d\-]+/machineTypes/[a-z\d\-]+$", machine_type):
            instance.machine_type = machine_type
        else:
            instance.machine_type = f"zones/{zone}/machineTypes/{machine_type}"

        instance.scheduling = compute_v1.Scheduling()
        if accelerators:
            instance.guest_accelerators = accelerators
            instance.scheduling.on_host_maintenance = (
                compute_v1.Scheduling.OnHostMaintenance.TERMINATE.name
            )

        if preemptible:
            # Set the preemptible setting
            warnings.warn(
                "Preemptible VMs are being replaced by Spot VMs.", DeprecationWarning
            )
            instance.scheduling = compute_v1.Scheduling()
            instance.scheduling.preemptible = True

        if spot:
            # Set the Spot VM setting
            instance.scheduling.provisioning_model = (
                compute_v1.Scheduling.ProvisioningModel.SPOT.name
            )
            instance.scheduling.instance_termination_action = instance_termination_action

        if custom_hostname is not None:
            # Set the custom hostname for the instance
            instance.hostname = custom_hostname

        if delete_protection:
            # Set the delete protection bit
            instance.deletion_protection = True

        # Prepare the request to insert an instance.
        request = compute_v1.InsertInstanceRequest()
        request.zone = zone
        request.project = project_id
        request.instance_resource = instance

        # Wait for the create operation to complete.
        print(f"Creating the {instance_name} instance in {zone}...")
        self.taskMessage("starting vm")
        operation = instance_client.insert(request=request)

        self.wait_for_extended_operation(operation, "instance creation")

        print(f"Instance {instance_name} created.")
        return instance_client.get(project=project_id, zone=zone, instance=instance_name)
# gcp = GCP()
# # gcp.create(1, "blah", "uglybitch")
# gcp.deleteVM("inyvtygirz")

# print(instance)

# print(private_key)https://portal.azure.com/?quickstart=true#blade/Microsoft_Azure_Billing/SubscriptionUpgradeBlade/azureSubscriptionId/6f15e407-5316-4a46-8972-d9a2d63cc29d/appId/AzPortal_UpgradeBtn
# print(instance.fingerprint)
# instance_client = compute_v1.InstancesClient()
# request = compute_v1.SetMetadataInstanceRequest(
#     instance="thing2",
#     project=project_ID,
#     zone="us-west1-b",
#     metadata_resource={"fingerprint":instance.fingerprint,
#                        "items":[{"key": "ssh", 
#                                  "value": str(public_key)
#                         }]}
# )

# instance_client = compute_v1.InstancesClient()
# instance_client.set_metadata(request=request)
