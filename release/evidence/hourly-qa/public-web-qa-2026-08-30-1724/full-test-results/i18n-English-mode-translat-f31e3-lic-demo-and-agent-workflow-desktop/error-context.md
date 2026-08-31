# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: i18n.spec.js >> English mode translates the public demo and agent workflow
- Location: tests\e2e\i18n.spec.js:3:5

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - generic [ref=e6]: ✤
      - text: PETi
    - generic [ref=e7]:
      - generic [ref=e8]: google-demo@example.test
      - generic [ref=e9]: G
      - button "Library" [ref=e10] [cursor=pointer]
      - button "Plan" [ref=e11] [cursor=pointer]
      - button "Share" [ref=e12] [cursor=pointer]
      - button "Help" [ref=e13] [cursor=pointer]
      - button "Settings" [ref=e14] [cursor=pointer]
      - button "Admin" [ref=e15] [cursor=pointer]
      - button "Sign out" [ref=e16] [cursor=pointer]
  - generic [ref=e17]:
    - complementary [ref=e18]:
      - navigation [ref=e19]:
        - button "⌂ Home" [ref=e20] [cursor=pointer]:
          - generic [ref=e21]: ⌂
          - text: Home
        - button "✦ Analyze" [ref=e22] [cursor=pointer]:
          - generic [ref=e23]: ✦
          - text: Analyze
        - button "◷ History" [ref=e24] [cursor=pointer]:
          - generic [ref=e25]: ◷
          - text: History
        - button "♙ Profile" [ref=e26] [cursor=pointer]:
          - generic [ref=e27]: ♙
          - text: Profile
        - button "✤ Agents" [ref=e28] [cursor=pointer]:
          - generic [ref=e29]: ✤
          - text: Agents
    - main [ref=e30]:
      - generic [ref=e31]:
        - generic [ref=e32]:
          - generic [ref=e33]:
            - strong [ref=e34]: PETi demo
            - generic [ref=e35]: Select a pet to explore its evidence.
          - generic [ref=e36]: 2 pets
        - generic [ref=e37]:
          - button "Luna Luna Golden retriever · Healthy" [ref=e38] [cursor=pointer]:
            - img "Luna" [ref=e39]
            - generic [ref=e40]:
              - text: Luna
              - generic [ref=e41]: Golden retriever · Healthy
          - button "Max Max Border collie · Needs observation" [ref=e42] [cursor=pointer]:
            - img "Max" [ref=e43]
            - generic [ref=e44]:
              - text: Max
              - generic [ref=e45]: Border collie · Needs observation
        - generic [ref=e46]:
          - generic [ref=e47]: "Evidence for Luna:"
          - button [ref=e48] [cursor=pointer]:
            - img "Evidencia 1 de Luna" [ref=e49]
          - button [ref=e50] [cursor=pointer]:
            - img "Evidencia 2 de Luna" [ref=e51]
          - button [ref=e52] [cursor=pointer]:
            - img "Evidencia 3 de Luna" [ref=e53]
          - button [ref=e54] [cursor=pointer]:
            - img "Evidencia 4 de Luna" [ref=e55]
          - button [ref=e56] [cursor=pointer]:
            - img "Evidencia 5 de Luna" [ref=e57]
      - generic [ref=e58]: Workspace
      - heading "PETi coordinates a review." [level=1] [ref=e59]
      - paragraph [ref=e60]: Each agent preserves state, evidence and safety review.
      - generic [ref=e61]:
        - generic [ref=e62]: No diagnosis or prescription. Conclusions require evidence and explicit limits.
        - heading "Multi-agent workflow" [level=2] [ref=e63]
        - generic [ref=e64]:
          - generic [ref=e65]:
            - generic [ref=e67]:
              - text: PETi coordinator
              - generic [ref=e68]: Receives the goal and delegates work.
            - generic [ref=e69]: ORCHESTRATOR
          - generic [ref=e70]:
            - generic [ref=e72]:
              - text: Evidence agent
              - generic [ref=e73]: Finds and organizes saved sources.
            - generic [ref=e74]: EVIDENCE
          - generic [ref=e75]:
            - generic [ref=e77]:
              - text: Specialist
              - generic [ref=e78]: Interprets only the requested capability.
            - generic [ref=e79]: SPECIALIST
          - generic [ref=e80]:
            - generic [ref=e82]:
              - text: Safety agent
              - generic [ref=e83]: Reviews uncertainty and warning signals.
            - generic [ref=e84]: SAFETY
        - button "Start review" [ref=e86] [cursor=pointer]
```