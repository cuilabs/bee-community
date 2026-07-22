"""Minimal Bee Python SDK quickstart — chat completion.

Run:
    pip install bee-sdk
    BEE_API_KEY=sk-bee-... python quickstart.py
"""

import os
import sys

from bee_sdk import BeeClient

api_key = os.environ.get("BEE_API_KEY")
if not api_key:
    print(
        "Set BEE_API_KEY first — issue one at "
        "https://bee.heossi.com/app/account/api-keys",
        file=sys.stderr,
    )
    sys.exit(1)

bee = BeeClient(api_key=api_key)

out = bee.chat.completions.create(
    model="bee-cell",
    messages=[
        {"role": "system", "content": "You are a precise assistant."},
        {"role": "user", "content": "Summarise the SOLID principles in 2 lines."},
    ],
    temperature=0.4,
)

print(out.choices[0].message.content)
print(
    f"\n[tokens prompt={out.usage.prompt_tokens} "
    f"completion={out.usage.completion_tokens}]",
)
