class ToolGateway:
    def __init__(self): self.tools = {}

    def register(self, name, handler, *, allowed_roles=None, mutating=False): self.tools[name] = {"handler": handler, "allowed_roles": set(allowed_roles or {"OWNER"}), "mutating": mutating}

    def invoke(self, name, args, *, actor_role="OWNER", approved=False):
        tool = self.tools.get(name)
        if not tool: raise ValueError("AGENT_TOOL_NOT_FOUND")
        if actor_role not in tool["allowed_roles"]: raise ValueError("AGENT_TOOL_FORBIDDEN")
        if tool["mutating"] and not approved: raise ValueError("AGENT_ACTION_APPROVAL_REQUIRED")
        if not isinstance(args, dict): raise TypeError("AGENT_TOOL_ARGUMENTS_INVALID")
        return tool["handler"](**args)
