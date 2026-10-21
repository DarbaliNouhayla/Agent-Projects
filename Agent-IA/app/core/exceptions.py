class AgentException(Exception):
    pass


class ToolExecutionError(AgentException):
    pass


class LLMConnectionError(AgentException):
    pass


class RateLimitExceeded(AgentException):
    pass
