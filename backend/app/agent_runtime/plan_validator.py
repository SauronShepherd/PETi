from app.agent_runtime.capability_registry import CapabilityRegistry


class PlanValidator:
    def __init__(self, capabilities: CapabilityRegistry):
        self.capabilities = capabilities

    def validate(self, nodes, *, requires_final_safety=True, max_steps=8):
        if not nodes or len(nodes) > max_steps:
            raise ValueError("AGENT_PLAN_BUDGET_EXCEEDED")
        ids = {node["node_id"] for node in nodes}
        if len(ids) != len(nodes):
            raise ValueError("AGENT_PLAN_DUPLICATE_NODE")
        visiting, visited = set(), set()
        by_id = {node["node_id"]: node for node in nodes}
        def visit(node_id):
            if node_id in visiting:
                raise ValueError("AGENT_PLAN_CYCLE")
            if node_id in visited:
                return
            visiting.add(node_id)
            node = by_id[node_id]
            for dependency in node.get("depends_on", []):
                if dependency not in by_id:
                    raise ValueError("AGENT_PLAN_DEPENDENCY_MISSING")
                visit(dependency)
            visiting.remove(node_id); visited.add(node_id)
        for node in nodes:
            if node.get("kind") and node["kind"] not in {"AGENT", "TOOL", "FUNCTION", "USER_INPUT", "USER_APPROVAL", "VALIDATOR"}:
                raise ValueError("AGENT_PLAN_NODE_KIND_INVALID")
            visit(node["node_id"])
            capability = self.capabilities.get(node["executor_id"], node.get("capability_version", "1.0.0"))
            if capability.mutation_scopes:
                raise ValueError("AGENT_AGENT_MUTATION_SCOPE_FORBIDDEN")
        if requires_final_safety and not any(node["executor_id"] == "FINAL_SYNTHESIS" for node in nodes):
            raise ValueError("AGENT_PLAN_FINAL_SAFETY_REQUIRED")
        return True
