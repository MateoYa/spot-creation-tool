import { FastifyLoggerInstance } from "fastify";
import { AWSManager } from "./AWS";
import { z } from "zod";
import { BasePlatform } from "./base/Platform";

export enum Provider {
  AWS = "aws",
  GCP = "gcp",
  Azure = "azure",
}

export const zProvider = z.enum([Provider.AWS, Provider.GCP, Provider.Azure]);

export function getProvider<T extends Provider>(
  provider: T,
  logger: FastifyLoggerInstance
): T extends Provider.AWS ? AWSManager : BasePlatform {
  if (provider === Provider.AWS) {
    return new AWSManager(logger);
  } else {
    throw new Error(`Provider "${provider}" not supported`);
  }
}
