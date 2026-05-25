from helloagents import (
    SimpleAgent, NPCProfile, ShortTermMemory, InMemoryLongTermMemory,
    MemoryManager, FavorabilitySystem, LLMClient, LLMConfig,
)


async def test_agent():
    profile = NPCProfile(
        npc_id="test_npc",
        name="TestBot",
        role="Debugger",
        personality_traits=["helpful", "precise"],
        background="A test NPC used for framework validation.",
        speech_style="Short, clear sentences.",
        private_knowledge=["The test suite is 87% green."],
        initial_greeting="Hello, I am a test.",
        favorability=0,
    )

    config = LLMConfig(
        api_key="sk-test",
        model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
    )
    llm = LLMClient(config)
    stm = ShortTermMemory(max_size=20)
    ltm = InMemoryLongTermMemory()
    mm = MemoryManager(stm, ltm, llm, short_term_window=10)
    fav = FavorabilitySystem(initial=0)
    agent = SimpleAgent(profile, mm, fav, llm)

    print("Agent created:", agent.profile.name)
    print("Favorability:", agent.favorability.score, agent.favorability.level_name())

    response = await agent.respond("Hello!")
    print("Reply:", response.reply)
    print("Fav delta:", response.favorability_change)
    print("Fav current:", response.favorability_current)

    await llm.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent())
