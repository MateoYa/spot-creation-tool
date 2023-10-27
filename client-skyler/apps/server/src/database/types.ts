import { Generated } from "kysely";
import { InstanceStatus, TaskStatus, TaskType } from "./enums";
import { Provider } from "../platforms";

export interface Database {
  AWSAPIKeys: AWSAPIKey;
  AWSCreateTask: AWSCreateTask;
  Task: Task;
  Instance: Instance;
}

export interface Task {
  id: Generated<string>;

  provider?: Provider;
  type: TaskType;

  instance?: string;
  task?: string;
}

export interface Instance {
  id: Generated<string>;
  status: InstanceStatus;

  ip: string;
  port: number;
  username: string;

  password?: string;
  ssh_key?: string;

  key_id: string;
  region: string;
  instanceId: string;
  provider: Provider;
}

export interface AWSCreateTask {
  id: Generated<string>;
  status: TaskStatus;
  amount: number;

  region: string;
  key_id: string;

  spotInstanceRequestId: string;
  instanceId?: string;
}

export interface AWSAPIKey {
  id: Generated<string>;
  targetInstances: number;
  currentInstances: number;

  accessKey: string;
  secretAccessKey: string;
}

export interface AWSInstance {
  id: Generated<string>;
  instanceId: string;
}
