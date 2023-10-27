import fp from 'fastify-plugin'
import { serializerCompiler, validatorCompiler, ZodTypeProvider } from "fastify-type-provider-zod";
import { ZodError } from 'zod';

export default fp(async (fastify) => {
  fastify.setValidatorCompiler(validatorCompiler);
  fastify.setSerializerCompiler(serializerCompiler);
  fastify.withTypeProvider<ZodTypeProvider>();

  fastify.setErrorHandler((error, request, reply) => {
    if (error instanceof ZodError) {
      fastify.log.info(`Request ${request.id} failed on validation: `, error.issues);

      return reply.status(400).send({
        statusCode: 400,
        error: "Bad Request",
        message: "Validation Error",
        issues: error.issues,
      });
    }

    fastify.log.error(`An error occured on "${request.url}"`);
    fastify.log.error(error);

    reply.status(500).send({
      statusCode: 500,
      error: "Internal Server Error",
      message: "An internal server error occured",
      _error: error
    });
  });
});

declare module 'fastify' {
  export interface FastifyTypeProviderDefault extends ZodTypeProvider { }
}