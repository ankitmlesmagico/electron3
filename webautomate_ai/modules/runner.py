# runner.py - The Core Automation Logic (API-Ready Library)

import asyncio
import logging
# We now import our new prompt builder
from modules.prompt_interpreter import build_agent_prompt
from modules.controller_setup import controller, browser_session, llm
from browser_use import Agent

logger = logging.getLogger("AUTOMATION_RUNNER")

async def run_high_level_task(user_goal: str):
    """
    Creates a single, powerful agent to accomplish a full, high-level goal.
    """
    await browser_session.start()

    # 1. Build the complete prompt using our dedicated hub.
    full_task_prompt = build_agent_prompt(user_goal)
    
    
    agent = Agent(
        task=full_task_prompt,
        llm=llm,
        controller=controller,
        browser_session=browser_session,
        use_vision=True,
    )
    
    # 3. Run the agent and let it handle the rest.
    await agent.run()
    
    logger.info("🎉 Agent has finished its task sequence.")