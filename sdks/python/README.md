# bee-sdk (Python)

Pointer page for the Python SDK. The package source lives in the main Bee repo at [`sdks/python/`](https://github.com/cuilabs/bee/tree/master/sdks/python).

## Install

The PyPI `cuilabs` organisation is currently **pending approval**, so `pip install bee-sdk` won't resolve yet. Until it lands, install directly from GitHub:

```bash
# Recommended while PyPI org approval is pending
pip install "git+https://github.com/cuilabs/bee.git#subdirectory=sdks/python"

# With the optional async client (adds httpx)
pip install "git+https://github.com/cuilabs/bee.git#subdirectory=sdks/python" httpx
```

Once PyPI approval lands, the canonical install becomes:

```bash
pip install bee-sdk          # sync, zero runtime deps
pip install bee-sdk[async]   # adds httpx for the async client
```

## Quickstart

```python
from bee_sdk import Bee

bee = Bee()  # reads BEE_API_URL + BEE_API_KEY from env

print(bee.chat(
    "Explain Shor's algorithm at NISQ depth",
    domain="quantum",
))
```

## More

- Marketing-site install + code samples: [bee.cuilabs.io/docs/sdks](https://bee.cuilabs.io/docs/sdks)
- Working examples: [`examples/python/`](../../examples/python)
- Source: [github.com/cuilabs/bee/tree/master/sdks/python](https://github.com/cuilabs/bee/tree/master/sdks/python)
