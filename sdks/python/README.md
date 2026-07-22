# bee-sdk (Python)

Pointer page for the Python SDK. The package is published on PyPI as [`bee-sdk`](https://pypi.org/project/bee-sdk/) — Python client + the `bee-mcp` MCP server in one zero-dependency package.

[![PyPI](https://img.shields.io/pypi/v/bee-sdk.svg)](https://pypi.org/project/bee-sdk/)

## Install

```bash
pip install bee-sdk          # sync client + bee-mcp server, zero runtime deps
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

## MCP server

The same package ships Bee's hosted MCP server:

```bash
export BEE_API_KEY=bee_sk_...   # create at bee.heossi.com/app/account/api-keys
bee-mcp                         # stdio — works with Claude Desktop, Cursor, VS Code, …
```

See [`../../mcp/`](../../mcp) for per-client configs.

## More

- Install + code samples: [bee.heossi.com/docs/sdks](https://bee.heossi.com/docs/sdks)
- Working examples: [`examples/python/`](../../examples/python)
- PyPI: [pypi.org/project/bee-sdk](https://pypi.org/project/bee-sdk/)
