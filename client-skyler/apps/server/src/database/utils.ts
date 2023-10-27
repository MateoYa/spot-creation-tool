import { sql } from "kysely";

export function sqliteEnum(name: string, values: string[]) {
  return sql`CHECK (${name} IN (${sql.join(values)}))`;
}