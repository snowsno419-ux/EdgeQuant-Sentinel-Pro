import Fastify from "fastify";
const app = Fastify({ logger: true });
app.get("/health", async () => ({status:"ok",service:"edgequant-webapp-api",environment:"phase1-prototype",tradingEnabled:false}));
app.get("/api/v1/readiness", async () => ({ liveMT5:"NOT_IMPLEMENTED", auth:"NOT_IMPLEMENTED",copyTrading:"NOT_IMPLEMENTED",database:"NOT_CONNECTED"}));
// No order-submission endpoints until auth, tenant isolation, idempotency, risk and broker reconciliation are implemented.
app.listen({port:Number(process.env.API_PORT||4000),host:"127.0.0.1"}).catch((error) => {app.log.error(error);process.exit(1)});
