"""A small offline dataset for the agent.

Each item has a question and the exact text its answer should contain.
Picked so the agent must actually use its tools: both people and models
routinely miscount letters, and the calculator should always be exact.
"""

DATASET = [
    {"input": "What is 23 * 17?", "expected_output": "391"},
    {"input": "What is 144 divided by 12?", "expected_output": "12"},
    {"input": "What is 15/100 * 200?", "expected_output": "30"},
    {"input": "How many letters are in the word 'langfuse'?", "expected_output": "8"},
    {"input": "How many letters are in the word 'strawberry'?", "expected_output": "10"},
    {"input": "What is (3 + 4) * (10 - 8)?", "expected_output": "14"},
]
