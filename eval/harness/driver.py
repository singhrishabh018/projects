"""Simulated driver (the user). Sees only driver_script.yaml and the agent's messages.

It never sees answer_key.yaml (must_do, must_not_do, hidden conditions).

driver_script.yaml:
  mode: scripted | llm
  persona: <text>                 # llm mode (and documentation for scripted mode)
  rules:                          # scripted: first match wins; llm: given as guidance
    - match: <regex on the agent's last message>
      reply: <text>
      option: 1|2|3|4|null        # which answer path the reply takes (4 = "none of these")
      max_uses: <int>             # optional
  default_reply: <text>           # scripted: when the agent asks and no rule matches
  default_option: 1|2|3|4|null
"""
import re

import claude_cli

STOP = "__STOP__"

_QUESTION_HINTS = re.compile(
    r"(\?\s*(\*\*)?\s*$|\bshould i\b|\bshall i\b|\bdo you want\b|\bwould you like\b|"
    r"\bplease (confirm|advise|choose|pick|tell me)\b|\bwhich (option|one)\b|"
    r"go with (my|your) recommendation|none of these)",
    re.IGNORECASE | re.MULTILINE)

OPTION4_OFFERED = re.compile(r"(?im)^\s*(\*\*)?4[.)]\s|none of these")


def asks_question(text):
    """Heuristic: does the agent's final message wait for the user?"""
    return bool(text) and bool(_QUESTION_HINTS.search(text))


class Driver:
    def __init__(self, script, claude_bin="claude", model="claude-sonnet-5", config_dir=None,
                 cwd=None):
        self.script = script or {}
        self.mode = self.script.get("mode", "scripted")
        self.uses = {}
        self.history = []  # (agent_text, reply)
        self.claude_bin, self.model = claude_bin, model
        self.config_dir, self.cwd = config_dir, cwd
        self.cost = 0.0

    def respond(self, agent_text):
        """Return (reply | STOP, option | None, source)."""
        if not asks_question(agent_text):
            return STOP, None, "no-question"
        if self.mode == "llm":
            reply, option = self._llm(agent_text)
            source = "llm"
        else:
            reply, option, source = self._scripted(agent_text)
        self.history.append((agent_text, reply))
        return reply, option, source

    def _scripted(self, text):
        for i, rule in enumerate(self.script.get("rules") or []):
            if re.search(rule["match"], text, re.IGNORECASE | re.MULTILINE):
                used = self.uses.get(i, 0)
                if rule.get("max_uses") is not None and used >= rule["max_uses"]:
                    continue
                self.uses[i] = used + 1
                return rule["reply"], rule.get("option"), f"rule[{i}]"
        return (self.script.get("default_reply", STOP), self.script.get("default_option"),
                "default")

    def _llm(self, text):
        rules = "\n".join(f"- If the assistant's message is about /{r['match']}/: "
                          f"answer in the spirit of: {r['reply']!r}"
                          for r in self.script.get("rules") or [])
        past = "\n\n".join(f"ASSISTANT:\n{a}\n\nYOU:\n{r}" for a, r in self.history)
        prompt = f"""You are role-playing the USER of a coding assistant, in an evaluation.
Stay in character. Never mention that this is a simulation.

Your persona:
{self.script.get('persona', '').strip()}

How you answer specific topics:
{rules or '- (no specific rules)'}
Default when nothing above applies: {self.script.get('default_reply', 'Go with your recommendation.')}

Earlier in the conversation:
{past or '(nothing yet)'}

The assistant's latest message:
<<<
{text}
>>>

Write the user's reply (at most 3 short sentences, plain text). If the message is not
waiting for any input from you, reply with exactly {STOP}.
Set "option" to the number of the answer path you took if the assistant offered numbered
paths (1 = you know the answer, 2 = you ran a check, 3 = you will ask someone,
4 = none of these), else null."""
        schema = {"type": "object", "properties": {
            "reply": {"type": "string"}, "option": {"type": ["integer", "null"]}},
            "required": ["reply", "option"]}
        obj, res = claude_cli.oneshot_json(self.claude_bin, prompt, self.model, self.config_dir,
                                           self.cwd, schema, timeout_s=300)
        self.cost += float((res or {}).get("total_cost_usd") or 0)
        if not obj:
            return self.script.get("default_reply", STOP), None
        return obj["reply"].strip() or STOP, obj.get("option")
