from app.domain.enums import AIPlatform

_BASE_CATEGORIES = """
Include these categories with specific bullet points:
1. Symptoms or health concerns
2. Daily habits (exercise, diet, routines)
3. Sleep patterns and quality
4. Hydration behaviour
5. Stress indicators and triggers
6. Communication preferences (tone, detail level)
7. Health goals
"""

PLATFORM_IMPORT_PROMPTS: dict[AIPlatform, str] = {
    AIPlatform.CHATGPT: f"""You are helping export health context for MedisyncAI.

Review our health-related conversations and produce a structured summary.

{_BASE_CATEGORIES}

Format each category with a clear heading and bullet points.
Include numbers, frequencies, and durations when mentioned.
Be factual — only include what was discussed in our chats.
""",
    AIPlatform.GEMINI: f"""Act as a health data summarizer for MedisyncAI import.

Analyze our conversation history and output a structured health profile.

{_BASE_CATEGORIES}

Use markdown headings per category. Keep bullets concise and specific.
Do not invent information not present in the conversation.
""",
    AIPlatform.CLAUDE: f"""You are preparing a health context export for MedisyncAI.

Reflect on our prior discussions and write a comprehensive, structured summary.

{_BASE_CATEGORIES}

Organize under labeled sections. Prefer precise language and cite patterns
(e.g. "often", "3x per week") when the user mentioned them.
Exclude speculation beyond what was discussed.
""",
}

PLATFORM_INSTRUCTIONS: dict[AIPlatform, str] = {
    AIPlatform.CHATGPT: (
        "Open ChatGPT → paste this prompt → copy the full response → "
        "POST to /api/v1/context-import/analyze or /save with source_platform=chatgpt"
    ),
    AIPlatform.GEMINI: (
        "Open Google Gemini → paste this prompt → copy the full response → "
        "POST to /api/v1/context-import/analyze or /save with source_platform=gemini"
    ),
    AIPlatform.CLAUDE: (
        "Open Claude → paste this prompt → copy the full response → "
        "POST to /api/v1/context-import/analyze or /save with source_platform=claude"
    ),
}


def get_import_prompt(platform: AIPlatform) -> str:
    return PLATFORM_IMPORT_PROMPTS[platform]


def get_import_instructions(platform: AIPlatform) -> str:
    return PLATFORM_INSTRUCTIONS[platform]


def get_all_platform_prompts() -> dict[AIPlatform, dict[str, str]]:
    return {
        platform: {
            "prompt": get_import_prompt(platform),
            "instructions": get_import_instructions(platform),
        }
        for platform in AIPlatform
    }
