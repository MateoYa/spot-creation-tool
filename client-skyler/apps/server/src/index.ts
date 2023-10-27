import 'dotenv/config';
import Fastify from "fastify";
import mainPlugin from "./app";

import { createLogger } from "bunyan";
import bunyanFormat from "bunyan-format";
import { Bindings, FastifyBaseLogger } from 'fastify/types/logger';

// create the logger
const logger = createLogger({
  name: "app",
  streams: [
    {
      level: "trace",
      stream: bunyanFormat({ outputMode: "short" })
    },
  ]
});

// add a no-op silent method to the logger
// this is required for fastify to work
export function createFastifyCompatibleLogger(log: typeof logger): FastifyBaseLogger {
  return {
    info: log.info.bind(log),
    error: log.error.bind(log),
    warn: log.warn.bind(log),
    debug: log.debug.bind(log),
    trace: log.trace.bind(log),
    fatal: log.fatal.bind(log),
    level: log.level().toString(),

    silent: () => { },
    child: (bindings: Bindings) => {
      return createFastifyCompatibleLogger(log.child(bindings));
    },
  };
}

// create fastify instance
const app = Fastify({
  disableRequestLogging: true,
  logger: {
    ...createFastifyCompatibleLogger(logger),
  },
});

// request logging
app.addHook("onRequest", (request, reply, done) => {
  logger.info({
    remoteAddress: request.ip,
    reqId: request.id,
    method: request.method,
  }, `Incoming request`);

  done();
});

app.addHook("onResponse", (request, reply, done) => {
  logger.info({
    reqId: request.id,
    responseTime: reply.getResponseTime()
  }, `${reply.statusCode} Reply sent`);

  done();
})

// register our main plugin
app.register(mainPlugin);

// and start listening
app.listen({
  port: process.env.PORT ? parseInt(process.env.PORT) : 3000
}).then(address => {
  app.log.info(`🚀 App listening on ${address}`);
});