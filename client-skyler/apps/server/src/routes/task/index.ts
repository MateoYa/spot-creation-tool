import { FastifyPluginAsync } from "fastify";
import { z } from "zod";
import { ZodTypeProvider } from "fastify-type-provider-zod";
import { TypeID } from "typeid-js";
import { db } from "../../database";
import { TaskType } from "../../database/enums";

const price: FastifyPluginAsync = async (fastify, opts): Promise<void> => {
  fastify.withTypeProvider<ZodTypeProvider>().get(
    "/status/:id",
    {
      schema: {
        params: z.object({
          id: z.string().regex(/^task\_[a-kmnp-z2-9]{26}$/),
        }),
      },
    },
    async function (request, reply) {
      // parse typeid
      const id = TypeID.fromString(request.params.id);

      // get task
      const task = await db
        .selectFrom("Task")
        .where("id", "=", id.toUUID())
        .selectAll()
        .executeTakeFirst();

      // check if task exists
      if (!task) {
        return reply.status(404).send({ error: "Task not found" });
      }

      // get platform
      switch (task.type) {
        case TaskType.PROVISION: {
        }
      }
    }
  );
};

export default price;
