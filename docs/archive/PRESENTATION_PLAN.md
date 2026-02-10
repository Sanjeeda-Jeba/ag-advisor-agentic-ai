# Slide Deck Plan: Agentic AI Project

## Slide 1 – Title & Vision
- Project name, logo (if available), presenter info
- One-liner vision: Streamlit-based conversational agent for agriculture intelligence

## Slide 2 – Problem & Motivation
- Challenges farmers face (fragmented data, unstructured queries)
- Need for real-time API access + conversational UX

## Slide 3 – Solution Overview
- High-level architecture diagram (Streamlit UI → LangGraph agent → API clients/LLM)
- Emphasize multi-tool orchestration, Tavily integration, USDA data

## Slide 4 – Key Features
- ChatGPT-style conversational UI with multi-chat sessions
- Tool matching & context handling for follow-ups
- API integrations: Weather, USDA Soil, Tavily CDMS, Agriculture web search

## Slide 5 – Technical Architecture (Detailed)
- Diagram layers: UI, Tool Matcher, Tool Executor, API Clients, LLM response generator
- Note session state, BaseAPIClient, credentials management

## Slide 6 – Data Flow / Tool Execution Example
- Step-by-step flow for a sample query (e.g., “Is Roundup safe?”)
- Include parsing, tool selection, Tavily request, LLM formatting

## Slide 7 – LLM & Prompt Engineering
- Models used (GPT-4o-mini default, override via env)
- Custom prompts for CDMS vs Agriculture responses, removal of redundant sections

## Slide 8 – UI/UX Enhancements
- Chat layout, new chat button, example questions placement
- Processing status steps, colorful input bar, follow-up handling

## Slide 9 – Implementation Highlights
- Key files: `streamlit_app_conversational.py`, `tool_matcher.py`, `llm_response_generator.py`, API clients
- Brief code snippets or bullet summaries per component

## Slide 10 – Testing & Validation
- Mention manual tests (Streamlit runs), unit scripts (`test_cdms_tavily.py`, etc.)
- Emphasize need for live API keys & sample runs

## Slide 11 – Challenges & Lessons Learned
- Dependency issues (conda constraints), USDA response parsing, Tavily key loading
- UX iterations based on user feedback

## Slide 12 – Next Steps & Roadmap
- LLM-based query parser proposal (from `LLM_QUERY_PARSER_PLAN.md`)
- Additional APIs (soil moisture, pest detection), telemetry, caching

## Slide 13 – Takeaways / Call to Action
- Impact summary (faster insights for agronomists/farmers)
- Invite adoption, contributions, or demo schedule

---
**Tips:**
- Keep slides concise, rely on visuals (screenshots, diagrams).
- Use appendices for detailed prompts/config snippets if needed.
- Have `.env`/credential instructions ready for live demo.
