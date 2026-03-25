// nomos-plugin/src/types.ts

// === OpenClaw Plugin SDK Types ===
// Defined locally because SDK is only available inside OpenClaw host process.

export interface PluginLogger {
  info(message: string): void;
  warn(message: string): void;
  error(message: string): void;
  debug(message: string): void;
}

export interface PluginCommandContext {
  senderId?: string;
  channel: string;
  isAuthorizedSender: boolean;
  args?: string;
  commandBody: string;
  config: Record<string, unknown>;
}

export interface PluginCommandResult {
  text?: string;
}

export interface PluginCommandDefinition {
  name: string;
  description: string;
  acceptsArgs?: boolean;
  requireAuth?: boolean;
  handler: (ctx: PluginCommandContext) => PluginCommandResult | Promise<PluginCommandResult>;
}

// === Hook Event Types ===

export interface HookBeforeAgentStartEvent {
  prompt: string;
  messages?: unknown[];
}

export interface HookBeforeAgentStartResult {
  systemPrompt?: string;
  prependContext?: string;
}

export interface HookBeforeToolCallEvent {
  toolName: string;
  params: Record<string, unknown>;
}

export interface HookBeforeToolCallContext {
  agentId?: string;
  sessionKey?: string;
  toolName: string;
}

export interface HookBeforeToolCallResult {
  params?: Record<string, unknown>;
  block?: boolean;
  blockReason?: string;
}

export interface HookAfterToolCallEvent {
  toolName: string;
  params: Record<string, unknown>;
  result: unknown;
  durationMs: number;
}

export interface HookToolResultPersistEvent {
  toolName: string;
  message: { role: string; content: string };
}

export interface HookToolResultPersistResult {
  message?: { role: string; content: string };
}

export interface HookMessageEvent {
  to?: string;
  from?: string;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface HookMessageSendingResult {
  cancel?: boolean;
  content?: string;
}

export interface HookSessionEvent {
  sessionKey: string;
  agentId?: string;
}

export interface HookAgentEndEvent {
  agentId?: string;
  messages?: unknown[];
  metadata?: Record<string, unknown>;
}

export interface HookGatewayEvent {
  version?: string;
}

// === Plugin API ===

export type HookHandler<E = unknown, R = void> =
  ((event: E, ctx: Record<string, unknown>) => R | void | Promise<R | void>);

export interface OpenClawPluginApi {
  id: string;
  name: string;
  version?: string;
  config: Record<string, unknown>;
  pluginConfig?: Record<string, unknown>;
  logger: PluginLogger;
  registerCommand: (command: PluginCommandDefinition) => void;
  registerCli: (registrar: unknown, opts?: { commands?: string[] }) => void;
  registerService: (service: { id: string; start: (ctx: unknown) => void; stop?: (ctx: unknown) => void }) => void;
  resolvePath: (input: string) => string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  on: (hookName: string, handler: HookHandler<any, any>, opts?: { priority?: number }) => void;
}
