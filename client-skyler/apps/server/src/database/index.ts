import { FileMigrationProvider, Kysely, Migrator, SqliteDialect } from "kysely";
import { Database } from "./types";
import SqliteDatabase from "better-sqlite3";
import { promises as fs } from "fs";
import * as path from "path";
import { FastifyBaseLogger } from "fastify";
// import KyselyUUIDPlugin from "./plugins/UUID";

// create the sqlite database
const sqliteDB = new SqliteDatabase('database.sqlite');

sqliteDB.pragma('journal_mode = WAL');
sqliteDB.loadExtension(path.join(__dirname, "../../sqlite-exts/uuidv7.so"))

// create the database client
export const db = new Kysely<Database>({
  dialect: new SqliteDialect({
    database: sqliteDB,
  }),

  plugins: [
    // KyselyUUIDPlugin
  ],

  log: ['query', 'error']
});

// migration
export async function migrateToLatest(logger: FastifyBaseLogger) {
  const migrator = new Migrator({
    db,
    provider: new FileMigrationProvider({
      fs,
      path,
      migrationFolder: path.join(__dirname, 'migrations'),
    })
  });

  logger.info('Running migrations...');
  const { error, results } = await migrator.migrateToLatest();

  // log the results
  results?.forEach((result) => {
    if (result.status === "Success") {
      logger.info(`Migration ${result.migrationName} was successful`);
    } else if (result.status === "Error") {
      logger.error(`Migration ${result.migrationName} failed.`);
    } else {
      logger.info(`Migration ${result.migrationName} was skipped.`);
    }
  });

  if (error) {
    logger.error(`Migration failed: ${error}`);
    return false;
  }

  // await db.insertInto("AWSTask")
  //   .values({
  //     spotInstanceId: "1",
  //     status: TaskStatus.RUNNING
  //   }).execute();

  return true;
}