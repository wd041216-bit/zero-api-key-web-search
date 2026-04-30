# npm Package

`zero-api-key-web-search` on npm is a thin Node.js wrapper around the Python package of the same name.

It exists so agent developers can use npm/npx workflows for the CLI and MCP server without maintaining a separate JavaScript implementation.

## Install

Install the Python runtime package first:

```bash
python -m pip install zero-api-key-web-search==20.0.0
```

Then install the npm wrapper globally:

```bash
npm install -g zero-api-key-web-search
```

You can also use it with `npx`:

```bash
npx zero-api-key-web-search zero-context "Python release" --goggles docs-first
npx zero-api-key-web-search zero-search "AI regulation news" --type news
npx zero-api-key-web-search zero-mcp
```

## Commands

The npm package exposes the same command names as the Python package:

| Command | Purpose |
| --- | --- |
| `zero-search` | Search the web. |
| `zero-context` | Build LLM-ready citation context. |
| `zero-browse` | Extract readable page text. |
| `zero-verify` | Check whether a claim looks supported or contested. |
| `zero-report` | Generate an evidence report. |
| `zero-mcp` | Start the MCP server. |

## MCP Example

```json
{
  "mcpServers": {
    "zero-api-key-web-search": {
      "command": "zero-mcp"
    }
  }
}
```

If your MCP client launches through npm instead of global bins:

```json
{
  "mcpServers": {
    "zero-api-key-web-search": {
      "command": "npx",
      "args": ["zero-api-key-web-search", "zero-mcp"]
    }
  }
}
```

## Why the npm package does not auto-install Python

The npm wrapper intentionally does not run `pip install` during `npm install`.

That keeps installation transparent, avoids cross-language supply-chain surprises, and lets users choose their Python environment.

If the Python package is missing, the wrapper prints:

```bash
python -m pip install zero-api-key-web-search==20.0.0
```

## Publishing Notes

Publish with a token stored outside the repository:

```bash
export NPM_TOKEN="..."
npm publish --access public
```

Never commit `.npmrc` or tokens to the repository.
