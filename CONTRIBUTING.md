# Contributing to bee-community

Thanks for picking up a thread on the public side of Bee. This repo collects examples, MCP install material, and SDK pointers — small, reviewable changes welcome.

## Where to file what

| Issue | File it here? |
|---|---|
| SDK bug (`@heossi/bee` or `bee-sdk`) | ✅ yes — open an issue with a minimal reproduction |
| MCP server bug or missing client config | ✅ yes |
| New example you'd like to contribute | ✅ yes — open a PR straight away |
| Bee engine bug, model output issue, billing question | ❌ no — use [bee.heossi.com/contact](https://bee.heossi.com/contact) |
| Security disclosure | ❌ not in public — email `bee-security@cuilabs.io` |

## Pull requests

1. Fork + branch from `main`.
2. Keep diffs small. Examples should be ≤ ~150 lines and runnable as-is.
3. Match existing tone in the example files — minimal comments, real working code, honest error messages.
4. PR description should answer: *what does this example demonstrate, and what does it deliberately leave out?*

## Honest-code expectations

We mirror the same rule the main Bee repo runs on:

> If a feature is shown in code or claimed in copy, it must actually work. No `TODO` / `FIXME` / `Math.random()` placeholder data, no fake function-calling examples, no "coming soon" labels unless the date is real.

Examples that depend on a feature that's still in flight should be tagged with the relevant [roadmap](https://bee.heossi.com/roadmap) stage and a clear status banner at the top of the file.

## License

By contributing, you agree your contribution is licensed under the [Apache-2.0](./LICENSE) of this repo.
