# GPT-4o-mini Migration Plan

## Goal
Switch the application's LLM from `gpt-3.5-turbo` to `gpt-4o-mini` for higher-quality responses while keeping configuration flexible.

## Steps
1. **Inventory current usage**
   - Identify all locations where `LLMResponseGenerator` is instantiated or where a default model string is set (currently `gpt-3.5-turbo`).
   - Confirm no other modules hardcode the model name.
2. **Update configuration**
   - Modify `LLMResponseGenerator` to default to `gpt-4o-mini`.
   - Optionally allow overriding via environment variable (e.g., `OPENAI_MODEL_NAME`) for future flexibility.
3. **Propagate changes**
   - Ensure all call sites either rely on the new default or read from configuration.
4. **Test the change**
   - Run a quick sanity test (e.g., `test_tavily_integration.py` or a minimal Streamlit run) to confirm responses still return successfully.
5. **Document update**
   - Update relevant docs (`README`, `TAVILY_*` guides) to mention the new default model.
