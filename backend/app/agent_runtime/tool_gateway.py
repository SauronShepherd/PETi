class ToolGateway:
    def __init__(self):
        self.tools = {}
        self._completed = {}

    def register(self, name, handler, *, allowed_roles=None, mutating=False): self.tools[name] = {"handler": handler, "allowed_roles": set(allowed_roles or {"OWNER"}), "mutating": mutating}

    def invoke(self, name, args, *, actor_role="OWNER", approved=False,
               owner_user_id=None, pet_id=None, expected_scope=None,
               idempotency_key=None):
        tool = self.tools.get(name)
        if not tool: raise ValueError("AGENT_TOOL_NOT_FOUND")
        if actor_role not in tool["allowed_roles"]: raise ValueError("AGENT_TOOL_FORBIDDEN")
        if tool["mutating"] and not approved: raise ValueError("AGENT_ACTION_APPROVAL_REQUIRED")
        if not isinstance(args, dict): raise TypeError("AGENT_TOOL_ARGUMENTS_INVALID")
        scope = expected_scope or {}
        if owner_user_id is not None and scope.get("owner_user_id") not in {None, owner_user_id}:
            raise ValueError("AGENT_TOOL_OWNER_SCOPE_MISMATCH")
        if pet_id is not None and scope.get("pet_id") not in {None, pet_id}:
            raise ValueError("AGENT_TOOL_PET_SCOPE_MISMATCH")
        if idempotency_key and idempotency_key in self._completed:
            return self._completed[idempotency_key]
        result = tool["handler"](**args)
        if idempotency_key:
            self._completed[idempotency_key] = result
        return result
