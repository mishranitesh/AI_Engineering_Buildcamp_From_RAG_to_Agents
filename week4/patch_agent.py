from pydantic_ai.usage import UsageLimits
import cost_tracker


INPUT_PRICE = 0.15   # $ per 1M input tokens
OUTPUT_PRICE = 0.60  # $ per 1M output tokens


def patch_agent(agent):

    agent.usage_limits = UsageLimits(
        request_limit=100,
        total_tokens_limit=200000,
    )

    original_run_sync = agent.run_sync

    def wrapped_run_sync(*args, **kwargs):

        result = original_run_sync(*args, **kwargs)

        try:
            usage = result.usage

            input_tokens = usage.input_tokens or 0
            output_tokens = usage.output_tokens or 0

            cost = (
                (input_tokens * INPUT_PRICE) / 1_000_000
                + (output_tokens * OUTPUT_PRICE) / 1_000_000
            )

            cost_tracker.TOTAL_COST += cost

            print(
                f"input={input_tokens}, "
                f"output={output_tokens}, "
                f"cost=${cost:.6f}"
            )

        except Exception as e:
            print(f"Could not track usage: {e}")

        return result

    agent.run_sync = wrapped_run_sync

    return agent