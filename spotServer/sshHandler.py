import paramiko
import os

class MySFTPClient(paramiko.SFTPClient):
    def put_dir(self, source, target, ssh_client):
        for item in os.listdir(source):
            if os.path.isfile(os.path.join(source, item)):
                self.put(os.path.join(source, item), '%s/%s' % (target, item))
                if item[-3:] == ".sh":
                    self.sendCommand(ssh_client, "chmod u+x " + '%s/%s' % (target, item))
            else:
                self.mkdir('%s/%s' % (target, item), ignore_existing=True)
                self.put_dir(os.path.join(source, item), '%s/%s' % (target, item))
        
    def mkdir(self, path, mode=511, ignore_existing=False):
        super(MySFTPClient, self).mkdir(path, mode)
    def sendCommand(self, ssh_client, command):
        stdin, stdout, stderr = ssh_client.exec_command(command)
        for line in stdout.readlines():
            print(line)

def configureServer(host, keypair):
    ssh_client = paramiko.SSHClient()
    # remote server credentials
    # ip = "34.227.207.205"
    # ip = ip.replace(".", "-")
    # host = "ec2-"+ip+".compute-1.amazonaws.com"
    print(host)
    username = "ubuntu"
    port = 22
    key = paramiko.RSAKey.from_private_key_file("./platforms/keypairs/"+keypair)
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, pkey=key)
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, pkey=key)
    print('connection established successfully')
    ftp = MySFTPClient.from_transport(transport)

    # you need full paths in order for this to work
    ftp.mkdir("/home/"+username+"/sftp_files")
    ftp.put_dir("/home/mateo/Desktop/spotServer/platforms/stfp_files", "/home/"+username+"/sftp_files", ssh_client)
    # stdin, stdout, stderr = ssh_client.exec_command("chmod u+x hello.sh")
    # for line in stdout.readlines():
    #     print(line)
    # stdin, stdout, stderr = ssh_client.exec_command("./hello.sh")
    # for line in stdout.readlines():
    #     print(line)
    ftp.close()
    ssh_client.close()