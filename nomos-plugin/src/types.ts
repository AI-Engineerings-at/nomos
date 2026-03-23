/**
 * OpenClaw Plugin SDK types — defined locally because the SDK package
 * is only available inside the OpenClaw host process.
 */

import type { Command } from "commander";

export interface OpenClawConfig {
  [key: string]: unknown;
}

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
  config: OpenClawConfig;
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

export interface PluginCliContext {
  program: Command;
  config: OpenClawConfig;
  workspaceDir?: string;
  logger: PluginLogger;
}

export type PluginCliRegistrar = (ctx: PluginCliContext) => void | Promise<void>;

export interface OpenClawPluginApi {
  id: string;
  name: string;
  version?: string;
  config: OpenClawConfig;
  pluginConfig?: Record<string, unknown>;
  logger: PluginLogger;
  registerCommand: (command: PluginCommandDefinition) => void;
  registerCli: (registrar: PluginCliRegistrar, opts?: { commands?: string[] }) => void;
  registerService: (service: { id: string; start: (ctx: unknown) => void; stop?: (ctx: unknown) => void }) => void;
  resolvePath: (input: string) => string;
  on: (hookName: string, handler: (...args: unknown[]) => void) => void;
}
