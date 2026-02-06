#!/usr/bin/env python3
"""Seed the database with initial prompts."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from services.common.db import get_engine


SEED_PROMPTS = [
    {
        "task_type": "code_generation",
        "content": (
            "You are a Python code generator. Given a user request, generate clean, working Python code.\n"
            "Include brief comments explaining key logic. Return ONLY the code block, no extra explanation."
        ),
        "version": 1,
        "is_active": True,
        "change_reason": "Initial seed prompt",
        "created_by": "system",
    },
]


async def seed():
    engine = get_engine()
    async with engine.begin() as conn:
        # Check if prompts already exist
        result = await conn.execute(text("SELECT COUNT(*) FROM prompts"))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} prompts. Skipping seed.")
            return

        for prompt in SEED_PROMPTS:
            await conn.execute(
                text(
                    "INSERT INTO prompts (task_type, content, version, is_active, change_reason, created_by) "
                    "VALUES (:task_type, :content, :version, :is_active, :change_reason, :created_by)"
                ),
                prompt,
            )
            print(f"Seeded prompt: {prompt['task_type']} v{prompt['version']}")

    await engine.dispose()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
