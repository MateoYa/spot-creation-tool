export enum TaskStatus {
  PENDING = "pending",
  COMPLETE = "complete",
}

export enum InstanceStatus {
  WAITING = "waiting",
  PROVISIONING = "provisioning",
  RUNNING = "running",
}

export enum TaskType {
  CREATE = "create",
  DELETE = "delete",
  /** SSH stage */
  SETUP = "setup",
  /** Provider setting up */
  PROVISION = "provision",
}
