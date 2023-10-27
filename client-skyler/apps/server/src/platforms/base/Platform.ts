import { FastifyBaseLogger } from "fastify";
import {
  CreateInstanceDetails,
  InstanceRequest,
  InstanceStatusDetails,
  InstanceStatusResponse,
} from "./Instance";
import { PriceData } from "./types";
import { TypeID } from "typeid-js";

export class BasePlatform {
  public static readonly PLATFORM_NAME: string = "base";

  protected logger: FastifyBaseLogger;

  /**
   * Creates a new platform
   * @param logger The logger to use for this platform
   */
  constructor(logger: FastifyBaseLogger) {
    const platform = (this.constructor as typeof BasePlatform).PLATFORM_NAME;

    this.logger = logger.child(
      {
        platform,
      },
      {
        msgPrefix: `[${platform}] `,
      }
    );
  }

  // pricing

  /**
   * Finds the cheapest spot price for the given regions
   * @param regions The regions to find the cheapest spot price for
   */
  findCheapestSpotPrice(regions: string[]): Promise<PriceData> {
    throw new Error("Not implemented");
  }

  // instance management

  /**
   * Creates a new instance provision request
   * @param details The details to use to create the instance
   */
  createInstance(
    details: CreateInstanceDetails,
    key: string
  ): Promise<InstanceRequest> {
    throw new Error("Not implemented");
  }

  /**
   * Gets the status of an instance
   * @param details The details of the instance
   */
  instanceStatus(
    details: InstanceStatusDetails
  ): Promise<InstanceStatusResponse> {
    throw new Error("Not implemented");
  }

  // API Key management
  // addKey(key: string): Promise<boolean> {
  //   throw new Error("Not implemented");
  // }

  // removeKey(key: string): Promise<boolean> {
  //   throw new Error("Not implemented");
  // }

  // utils
  protected uuidToTypeID(uuid: string): string {
    const platform = (this.constructor as typeof BasePlatform).PLATFORM_NAME;
    return TypeID.fromUUID(uuid, platform).toString();
  }

  public typeIdToUUID(typeId: string): string {
    const platform = (this.constructor as typeof BasePlatform).PLATFORM_NAME;
    const parsed = TypeID.fromString(typeId);

    if (parsed.getType() != platform) {
      throw new Error("Invalid type ID");
    }

    return parsed.toUUID();
  }
}
