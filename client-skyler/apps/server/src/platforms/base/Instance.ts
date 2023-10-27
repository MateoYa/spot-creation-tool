export enum InstanceStatus {
  /** The instance is running. */
  Running = "running",

  /** The instance is provisioning. */
  Provisioning = "provisioning",

  /** The instance is being set up */
  SettingUp = "setting-up",

  /** An error occured or the instance entered an invalid state */
  Error = "error",
}

export interface Instance {
  /** The globally unique ID of the instance. */
  id: string;

  /** The platform the instance was created on. */
  platform: string;

  /** The instance's IP address */
  ip: string;

  /** The instance status */
  status: InstanceStatus;
}

export type InstanceRequest = {
  /** The ID of the instance */
  uuid: string;
  typeid: string;
}

export type InstanceStatusDetails = {
  /** The UUID ID of the task. */
  id: string;
}

export type InstanceStatusResponseSuccess = {
  /** The status of the instance. */
  status: InstanceStatus.Running | InstanceStatus.SettingUp;

  /** The IP address of the instance. */
  ip: string;

  /** The ID of the instance. */
  id: string;
}

export type InstanceStatusResponsePending = {
  /** The status of the instance. */
  status: InstanceStatus.Provisioning;
}

export type InstanceStatusResponse = InstanceStatusResponseSuccess | InstanceStatusResponsePending;

export type CreateInstanceDetails = {
  /** The region to create the instance in. */
  region: string;

  /** The amount of instances to create */
  amount: number;
}