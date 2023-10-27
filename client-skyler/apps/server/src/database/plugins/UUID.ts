import { uuidv7 } from "@kripod/uuidv7";
import { InsertQueryNode, KyselyPlugin, OperationNodeTransformer } from "kysely";
import { inspect } from "node:util";

// const COLUMN_NAME_MAP = [["AWSTask", "id"]];
const TABLE_COLUMN_MAP = {
  AWSTask: "id"
} as {
  [tableName: string]: string;
}

class UUIDTransformer extends OperationNodeTransformer {
  protected transformInsertQuery(node: InsertQueryNode): InsertQueryNode {
    node = super.transformInsertQuery(node);

    // now check if the table is AWSTask 
    const tableName = node.into.table.identifier.name;

    if (tableName in TABLE_COLUMN_MAP) {
      const columnName = TABLE_COLUMN_MAP[tableName];

      // check if the column is not already defined
      if (!node.columns?.some((column) => column.column.name === columnName)) {
        // add the column

        // @ts-ignore
        node.columns = [
          ...node.columns ?? [],
          {
            kind: "ColumnNode",
            column: {
              kind: "IdentifierNode",
              name: columnName,
            }
          }
        ];

        // add the value
        // @ts-ignore 
        let values = super.transformValues(node.values);

        // @ts-ignore
        values.values = [
          {
            ...values.values[0],
            values: [
              ...values.values[0].values ?? [],
              uuidv7()
            ]
          },
          ...values.values.slice(1),
        ];

        // @ts-ignore
        node.values = values;

        console.log(inspect(node, { depth: Infinity }))
      }
    }

    return node;
  }
}

const KyselyUUIDPlugin: KyselyPlugin = {
  // @ts-ignore
  transformQuery: (query) => {
    return new UUIDTransformer().transformNode(query.node);
  },

  transformResult: async (result) => {
    return result.result;
  }
}

export default KyselyUUIDPlugin;