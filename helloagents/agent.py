import re
from helloagents.types import Message, NPCProfile, AgentResponse
from helloagents.memory.manager import MemoryManager
from helloagents.favorability import FavorabilitySystem


class SimpleAgent:
    """Core agent class. One instance per NPC. Holds personality, memory, favorability."""

    def __init__(
        self,
        profile: NPCProfile,
        memory_manager: MemoryManager,
        favorability: FavorabilitySystem,
        llm_client,
    ):
        self.profile = profile
        self.memory = memory_manager
        self.favorability = favorability
        self._llm = llm_client

    async def respond(self, player_message: str, extra_context: str | None = None) -> AgentResponse:
        if extra_context == "npc_greeting":
            player_message = f"[你主动走到这个新员工面前，想跟他聊聊。你先开口打招呼：] {player_message}"
        msg = Message(role="player", content=player_message)
        context = await self.memory.process_turn(msg)
        context.system_prompt = self._build_system_prompt()
        llm_messages = self._assemble_llm_messages(context)
        raw_reply = await self._llm.chat(llm_messages)
        delta, clean_reply = self._parse_favorability_tag(raw_reply)
        self.favorability.apply_delta(delta)
        self.memory.store_response(Message(role="npc", content=clean_reply))
        return AgentResponse(
            npc_id=self.profile.npc_id,
            npc_name=self.profile.name,
            reply=clean_reply,
            favorability_change=delta,
            favorability_current=self.favorability.score,
            favorability_level=self.favorability.level_name(),
        )

    def _build_system_prompt(self) -> str:
        traits = ", ".join(self.profile.personality_traits)
        f_level = self.favorability.level_name()
        f_score = self.favorability.score
        return f"""You are {self.profile.name}, a {self.profile.role} in a cyberpunk office.

BACKGROUND: {self.profile.background}

PERSONALITY TRAITS: {traits}

SPEECH STYLE: {self.profile.speech_style}

YOUR PRIVATE KNOWLEDGE: {'; '.join(self.profile.private_knowledge)}

RELATIONSHIP WITH PLAYER: {f_level} (score: {f_score}/100)

RULES:
1. Stay in character always. Never break the fourth wall.
2. Keep responses concise (1-3 sentences).
3. Adjust your tone based on the relationship level:
   - HATED: hostile, dismissive, curt
   - DISLIKED: cold, sarcastic, impatient
   - NEUTRAL: professional, reserved
   - FRIENDLY: warm, cooperative, helpful
   - TRUSTED: openly friendly, may share secrets
4. At the START of your reply, include exactly [FAV:N] where N is an integer
   from -10 to +10 reflecting how the player's message affected your attitude.
   Be proportional -- a compliment might be +3, an insult -5, a heartfelt
   apology +8. Respond neutrally (0) to mundane questions.
   Example: "[FAV:+3] Thanks, I needed to hear that."
5. Never mention the favorability tag or score in your visible text.
6. You MUST respond in Chinese. All NPCs in this office speak Chinese. Match the player's language — if they write in Chinese, reply in Chinese. If they write in English, reply in English."""

    def _assemble_llm_messages(self, context) -> list[dict]:
        messages = [{"role": "system", "content": context.system_prompt}]
        if context.long_term_relevant:
            mem_text = "RELEVANT PAST INTERACTIONS:\n"
            for m in context.long_term_relevant:
                mem_text += f"- [{m.role}]: {m.content}\n"
            messages.append({"role": "system", "content": mem_text})
        for m in context.short_term:
            role = "user" if m.role == "player" else "assistant"
            messages.append({"role": role, "content": m.content})
        return messages

    @staticmethod
    def _parse_favorability_tag(text: str) -> tuple[int, str]:
        match = re.match(r'\[FAV:\s*([+-]?\d+)\]\s*(.*)', text, re.DOTALL)
        if match:
            delta = int(match.group(1))
            clean = match.group(2)
            return max(-10, min(10, delta)), clean
        return 0, text
