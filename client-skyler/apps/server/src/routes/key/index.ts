import { FastifyPluginAsync } from "fastify";
import { z } from "zod";
import { ZodTypeProvider } from "fastify-type-provider-zod";
import { db } from "../../database";
import { Provider, getProvider } from "../../platforms";

const key: FastifyPluginAsync = async (fastify, opts): Promise<void> => {
  fastify
    .withTypeProvider<ZodTypeProvider>()
    .get("/list", async function (request, reply) {
      // get all keys
      const keys = await db.selectFrom("AWSAPIKeys").selectAll().execute();

      // return keys
      return keys;
    })
    .post(
      "/aws/add",
      {
        schema: {
          body: z.object({
            accessKey: z.string(),
            secretAccessKey: z.string(),
          }),
        },
      },
      async function (request, reply) {
        // create key
        const manager = getProvider(Provider.AWS, fastify.log);

        const key = await manager.addKey(
          request.body.accessKey,
          request.body.secretAccessKey
        );

        reply.send({ key });
      }
    )
    .delete(
      "/aws/remove/:key",
      {
        schema: {
          params: z.object({
            key: z.string(),
          }),
        },
      },
      async function (request, reply) {
        // create key
        const manager = getProvider(Provider.AWS, fastify.log);

        const result = await manager.removeKey(request.params.key);

        if (!result) {
          reply.status(404);
        }

        reply.send({ success: true });
      }
    );
};

export default key;
