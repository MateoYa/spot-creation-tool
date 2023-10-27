import { Kysely } from "kysely";

export async function up(db: Kysely<any>): Promise<void> {
  await db.schema
    .createTable("AWSAPIKey")
    .addColumn("id", "text", (eb) =>
      eb.primaryKey().defaultTo("uuid_generate_v7()")
    )
    .addColumn("accessKey", "text", (eb) => eb.notNull())
    .addColumn("secretAccessKey", "text", (eb) => eb.notNull())
    .execute();

  await db.schema
    .createTable("InstanceSetupTask")
    .addColumn("id", "text", (eb) =>
      eb.primaryKey().defaultTo("uuid_generate_v7()")
    )
    .addColumn("status", "text")
    .addColumn("ip", "text")
    .addColumn("port", "integer")
    .addColumn("username", "text")
    .addColumn("password", "text")
    .addColumn("ssh_key", "text")
    .execute();

  await db.schema
    .createTable("AWSCreateTask")
    .addColumn("id", "text", (eb) =>
      eb.primaryKey().defaultTo("uuid_generate_v7()")
    )
    .addColumn("status", "text")
    .addColumn("region", "text")
    .addColumn("key_id", "text")
    .addColumn("spotInstanceRequestId", "text")
    .addColumn("instanceId", "text")
    .execute();

  await db.schema
    .createTable("Task")
    .addColumn("id", "text", (eb) =>
      eb.primaryKey().defaultTo("uuid_generate_v7()")
    )
    .addColumn("to", "text")
    .execute();
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable("AWSTask").execute();
  await db.schema.dropTable("InstanceSetupTask").execute();
  await db.schema.dropTable("AWSAPIKey").execute();
  await db.schema.dropTable("Task").execute();
}
