const LOG_LEVELS = ["debug", "info", "warn", "error"] as const;
type LogLevel = (typeof LOG_LEVELS)[number];

function shouldLog(level: LogLevel): boolean {
  if (process.env.NODE_ENV === "test") return level === "error";
  return true;
}

function log(level: LogLevel, ...args: unknown[]): void {
  if (!shouldLog(level)) return;
  const prefix = `[${level.toUpperCase()}]`;
  const method = level === "error" ? console.error : level === "warn" ? console.warn : console.log;
  method(prefix, new Date().toISOString(), ...args);
}

export const logger = {
  debug: (...args: unknown[]) => log("debug", ...args),
  info: (...args: unknown[]) => log("info", ...args),
  warn: (...args: unknown[]) => log("warn", ...args),
  error: (...args: unknown[]) => log("error", ...args),
};
