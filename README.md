# spot-creation-tool
as this tool is meant to be able to work with aws/azure/gcp there is 3 sepreate linking guides


so you need the following:
## Program 1
- Runs as a service so it can constantly check the status of spot instances.
  - Will expose an HTTP endpoint that the CLI tool will use. For secure access, you will need to install a reverse proxy like nginx to handle SSL
- Needs some sort of API server so the CLI tool can communicate with it
- When requested, it can spin up more spot instances on: AWS, GCP, and Azure depending on what you choose.
  - Once deployed, it will setup your SSH keys and then SSH into the server.
  - Using SFTP, it will transfer your bash script.
  - Afterwards, it will run your bash script.
  - It will monitor the output of the script looking for some sort of message saying that the health check has passed.
- If a spot instance is terminated
  - it will automatically request a new spot instance from the same provider and run the same steps from above.

## Program 2
- CLI tool that communicates with service
- `spot-tool setup`
  - sets up the CLI (you give it the URL address of the service)
  - the tool will save this information.
  
done
- `spot-tool create <aws/gcp/azure> <amount> <key-id>`
   - tells the service to create `<amount>` new instances on whatever platform you want. Will return you a task ID that you can use to track the deployment progress.
   - Uses the API key that you specify.
   
easy update status on database (lightwork)
- `spot-tool status all`
  - Shows a list of all instances currently running as well as any tasks.
- `spot-tool status task <task-id>`
  - Shows you the progress of a deployment task (details like how many successful deployments so far, status of each new deployment, etc)


easy DONE

  
easy
- `spot-tool terminate deployment <deployment-id>`
  - Stops a deployment and destroys all spot instances in the deployment.
- `spot-tool terminate all`
  - Stops **all** instances across all API keys



kinda confusing


 
 done
 - `spot-tool terminate individual <server-id/ip>` *
- Terminates a single server by it's ID (shown in the status all command) 
- `spot-tool terminate key <api-key>`*
  - Terminates all instances on the given API key
- `spot-tool api-key list` *
  - Lists all API keys
  
  
  bullshit not doing it
- `spot-tool api-key add <gcp/aws/azure> <key>`
  - Registers a new key
- `spot-tool api-key delete <gcp/aws/azure> <key>`
  - Deletes a key