import assert = require("assert");
import {
  CreateInstanceDetails,
  InstanceRequest,
  InstanceStatus,
  InstanceStatusDetails,
  InstanceStatusResponse,
} from "./base/Instance";
import { BasePlatform } from "./base/Platform";
import {
  EC2Client,
  DescribeSpotPriceHistoryCommand,
  DescribeSpotPriceHistoryCommandOutput,
  RequestSpotInstancesCommand,
  DescribeInstancesCommand,
  DescribeSpotInstanceRequestsCommand,
} from "@aws-sdk/client-ec2";
import { isDefined } from "../utils";
import { db } from "../database";
import {
  TaskStatus,
  InstanceStatus as DBInstanceStatus,
  TaskType,
} from "../database/enums";
import { TypeID } from "typeid-js";
import { Provider } from ".";

// type KeyDetails = {
//   accessKey: string;
//   secretAccessKey: string;
// }

export class AWSManager extends BasePlatform {
  public static readonly PLATFORM_NAME = "aws";
  public static readonly INSTANCE_TYPE = "t2.micro";

  // Debian 11 (Bullseye) (64-bit (x86))
  public static readonly IMAGE_ID = "ami-0395877f2f2fb194a";
  public static readonly SSH_USER = "admin";
  public static readonly SSH_KEY = "REPLACE-ME";

  async findCheapestSpotPrice(regions: string[]) {
    this.logger.info(`Finding cheapest spot price for ${regions.join(", ")}`);

    // create a bunch of clients since they are region bound
    const clients = regions.map((region) => new EC2Client({ region }));

    // now create the command to run
    const command = new DescribeSpotPriceHistoryCommand({
      InstanceTypes: ["t2.micro"],
    });

    // and run it for each client
    const responses = await Promise.allSettled(
      clients.map((client) => client.send(command))
    );

    // filter successful regions
    const prices = responses
      .filter(
        (
          response
        ): response is PromiseFulfilledResult<DescribeSpotPriceHistoryCommandOutput> =>
          response.status === "fulfilled"
      )
      .map((d) => d.value);

    // find all the failed regions
    const failedRegions = responses
      .map((response, index) => {
        if (response.status === "rejected") {
          this.logger.info(
            `Region "${regions[index]}" failed:`,
            response.reason
          );

          return {
            region: regions[index],
            error: response.reason,
          };
        }

        return null;
      })
      .filter(isDefined);

    // find the cheapest
    const cheapest = prices.reduce((cheapest, current) => {
      const currentPrice = current.SpotPriceHistory?.[0]?.SpotPrice;
      const cheapestPrice = cheapest.SpotPriceHistory?.[0]?.SpotPrice;

      if (!currentPrice) {
        return cheapest;
      }

      if (!cheapestPrice) {
        return current;
      }

      return currentPrice < cheapestPrice ? current : cheapest;
    }, prices[0]);

    // validate
    assert(cheapest.SpotPriceHistory?.[0]?.AvailabilityZone, "No region found");
    assert(cheapest.SpotPriceHistory?.[0]?.SpotPrice, "No price found");

    // format and return
    return {
      region: cheapest.SpotPriceHistory[0].AvailabilityZone,
      price: cheapest.SpotPriceHistory[0].SpotPrice,
      warnings: failedRegions,
    };
  }

  async createInstance(
    details: CreateInstanceDetails,
    keyId: string
  ): Promise<InstanceRequest> {
    this.logger.info(`Creating instance in ${details.region}`);
    const command = new RequestSpotInstancesCommand({
      InstanceCount: details.amount,
      Type: "one-time",
      LaunchSpecification: {
        ImageId: AWSManager.IMAGE_ID,
        InstanceType: AWSManager.INSTANCE_TYPE,
      },
    });

    // create the ec2 client
    const client = await this.createClient(details.region, keyId);
    this.logger.info(
      `Requesting ${details.amount} instances in ${details.region}`
    );
    const response = await client.send(command);
    this.logger.info(`Received response: ${response.$metadata.httpStatusCode}`);

    const instance = response.SpotInstanceRequests?.[0];

    // verify
    assert(instance !== undefined, "No instance returned");
    assert(
      instance.SpotInstanceRequestId !== undefined,
      "No instance ID returned"
    );

    // add to database
    const task = await db
      .insertInto("AWSCreateTask")
      .values({
        status: TaskStatus.PENDING,
        region: details.region,
        key_id: keyId,
        spotInstanceRequestId: instance.SpotInstanceRequestId,
        amount: details.amount,
      })
      .returning("id")
      .execute();

    await db
      .updateTable("AWSAPIKeys")
      .set((eb) => ({
        targetInstances: eb("targetInstances", "+", details.amount),
      }))
      .where("id", "=", keyId)
      .execute();

    return {
      typeid: TypeID.fromUUID(AWSManager.PLATFORM_NAME, task[0].id).toString(),
      uuid: task[0].id,
    };
  }

  /**
   *
   * @param details Expects the AWSCreateTask ID (parsed)
   * @returns
   */
  async instanceStatus(
    details: InstanceStatusDetails
  ): Promise<InstanceStatusResponse> {
    const taskDetails = await db
      .selectFrom("AWSCreateTask")
      .where("id", "=", details.id)
      .select([
        "region",
        "instanceId",
        "spotInstanceRequestId",
        "status",
        "key_id",
      ])
      .execute();

    assert(taskDetails.length === 1, "No task found");

    const keyId = taskDetails[0].key_id;

    // turn the spot instance ID into an instance ID
    const client = await this.createClient(taskDetails[0].region, keyId);
    const toInstanceResponse = await client.send(
      new DescribeSpotInstanceRequestsCommand({
        SpotInstanceRequestIds: [taskDetails[0].spotInstanceRequestId],
      })
    );

    const instanceId = toInstanceResponse.SpotInstanceRequests?.[0]?.InstanceId;

    // verify
    if (instanceId === undefined) {
      return {
        status: InstanceStatus.Provisioning,
      };
    }

    const response = await client.send(
      new DescribeInstancesCommand({
        InstanceIds: [instanceId],
      })
    );

    const instance = response.Reservations?.[0]?.Instances?.[0];

    // verify
    assert(instance !== undefined, "No instance returned");
    assert(instance.State !== undefined, "No instance state returned");

    if (instance.State.Name === "running") {
      assert(instance.PublicIpAddress !== undefined, "No IP address returned");

      // update the database
      if (taskDetails[0].status === TaskStatus.PENDING) {
        const [{ id }] = await db
          .insertInto("Instance")
          .values({
            status: DBInstanceStatus.WAITING,
            ip: instance.PublicIpAddress,
            port: 22,
            username: AWSManager.SSH_USER,
            ssh_key: AWSManager.SSH_KEY,

            provider: Provider.AWS,
            instanceId,
            region: taskDetails[0].region,
            key_id: keyId,
          })
          .returning("id")
          .execute();

        await db
          .updateTable("AWSCreateTask")
          .set({
            status: TaskStatus.COMPLETE,
            instanceId,
          })
          .where("id", "=", details.id)
          .execute();

        await db
          .updateTable("Task")
          .set({
            provider: undefined,
            type: TaskType.SETUP,
            task: id,
          })
          .execute();
      }

      return {
        status: InstanceStatus.Running,
        ip: instance.PublicIpAddress,
        id: instanceId,
      };
    }

    return {
      status: InstanceStatus.Provisioning,
    };
  }

  async runTask(reschedule = true) {
    const startTime = Date.now();

    // check pending create tasks
    const pendingTasks = await db
      .selectFrom("AWSCreateTask")
      .where("status", "=", TaskStatus.PENDING)
      .selectAll()
      .execute();

    for (const task of pendingTasks) {
      // force recheck the status
      await this.instanceStatus({ id: task.id });
    }

    this.logger.info(
      `Checked ${pendingTasks.length} pending tasks in ${
        Date.now() - startTime
      }ms`
    );

    // reschedule the task
    if (reschedule) {
      setTimeout(
        () => this.runTask(),
        parseInt(process.env.TASK_INTERVAL ?? (5 * 60 * 1000).toString())
      );
    }
  }

  async addKey(accessKey: string, secretKey: string): Promise<string> {
    const details = await db
      .insertInto("AWSAPIKeys")
      .values({
        accessKey,
        secretAccessKey: secretKey,
        targetInstances: 0,
        currentInstances: 0,
      })
      .returning("id")
      .execute();

    return details[0].id;
  }

  async removeKey(key: string): Promise<boolean> {
    const result = await db
      .deleteFrom("AWSAPIKeys")
      .where("id", "=", key)
      .execute();

    return result.length === 1;
  }

  async getKey(keyId: string) {
    const result = await db
      .selectFrom("AWSAPIKeys")
      .where("id", "=", keyId)
      .selectAll()
      .executeTakeFirst();

    if (!result) {
      throw new Error("No key found");
    }

    return result;
  }

  async testKey(key: string): Promise<boolean> {
    const keyDetails = await this.getKey(key);

    const client = new EC2Client({
      credentials: {
        accessKeyId: keyDetails.accessKey,
        secretAccessKey: keyDetails.secretAccessKey,
      },
      region: "eu-west-1",
    });

    try {
      await client.send(new DescribeInstancesCommand({}));
    } catch (e) {
      return false;
    }

    return true;
  }

  // util functions
  private async createClient(region: string, keyId: string) {
    const key = await this.getKey(keyId);

    return new EC2Client({
      region,
      credentials: {
        accessKeyId: key.accessKey,
        secretAccessKey: key.secretAccessKey,
      },
    });
  }
}
