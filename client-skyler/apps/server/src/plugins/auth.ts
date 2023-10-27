import fp from 'fastify-plugin'

const TOKEN = process.env.TOKEN;

export default fp(async (fastify, opts) => {

  if (!TOKEN) {
    fastify.log.warn('No token provided, authentication is disabled!');
    return;
  }

  fastify.addHook('preHandler', (req, rep, done) => {
    // check if this route needs authentication
    // opt-out type option
    if (req.context.config.auth === false) {
      return done();
    }

    // check the header
    const [type, token] = req.headers['authorization']?.split(' ') ?? [];

    if (type !== 'Bearer' || token !== TOKEN) {
      return rep.status(401).send({
        error: 'Unauthorized',
        message: 'Invalid token',
      });
    }

    done();
  });
})

declare module 'fastify' {
  export interface FastifyContextConfig {
    auth?: boolean;
  }
}