# Plan: Remove "Answer to your question" Heading

1. **Locate current formatting**
   - Open `src/tools/llm_response_generator.py` and inspect `_generate_agriculture_web_response`.
   - Identify the system prompt block that instructs the LLM to include the "**Answer to your question:**" heading.

2. **Update prompt format**
   - Modify the instructions so the response begins directly with a concise summary paragraph (no explicit heading).
   - Keep the rest of the structure (Key Points, Recommended Approach, Learn More, Pro Tip) to preserve clarity.

3. **Verify consistency**
   - Ensure no other parts of the code insert the old heading.
   - Save changes and (optionally) rerun a quick prompt test later to confirm the new format.
