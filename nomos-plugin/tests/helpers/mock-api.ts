// nomos-plugin/tests/helpers/mock-api.ts
import { createServer, type Server, type IncomingMessage, type ServerResponse } from "node:http";

export function createMockApiServer(port: number) {
  let server: Server;

  function handler(req: IncomingMessage, res: ServerResponse) {
    let body = "";
    req.on("data", (chunk: Buffer) => { body += chunk.toString(); });
    req.on("end", () => {
      const url = req.url ?? "";
      res.setHeader("Content-Type", "application/json");

      if (url.includes("/api/compliance/gate")) {
        res.end(JSON.stringify({ passed: true, missing: [] }));
      } else if (url.includes("/api/audit/entry")) {
        res.end(JSON.stringify({ hash: "abc123def456", id: "audit-1" }));
      } else if (url.includes("/api/pii/filter")) {
        const parsed = JSON.parse(body);
        const filtered = (parsed.text as string).replace(/[\w.+-]+@[\w.-]+\.\w+/g, "[EMAIL_REDACTED]");
        const found = filtered !== parsed.text ? [{ type: "email", position: [0, 0] }] : [];
        res.end(JSON.stringify({ filtered, found }));
      } else if (url.includes("/api/budget/check")) {
        res.end(JSON.stringify({ allowed: true, remaining: 45.50 }));
      } else if (url.includes("/api/agents") && url.includes("/heartbeat")) {
        res.end(JSON.stringify({ ok: true }));
      } else if (url.includes("/api/incidents")) {
        res.end(JSON.stringify({ id: "incident-1", created: true }));
      } else if (url.includes("/api/health")) {
        res.end(JSON.stringify({ status: "ok" }));
      } else {
        res.statusCode = 404;
        res.end(JSON.stringify({ error: "not found" }));
      }
    });
  }

  return {
    start: () => new Promise<void>((resolve) => {
      server = createServer(handler);
      server.listen(port, resolve);
    }),
    stop: () => new Promise<void>((resolve) => {
      server.close(() => resolve());
    }),
  };
}
