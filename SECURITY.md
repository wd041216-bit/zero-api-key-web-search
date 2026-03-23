# Security Policy

## Reporting

If you find a security issue, please open a private report through GitHub security advisories if available, or contact the maintainer before publishing details.

## Scope

Security-sensitive areas in this repository include:

- TLS handling in `browse-page`
- MCP server behavior and exposed tool contracts
- command execution and packaging surfaces

## Notes

- TLS verification is enabled by default.
- Insecure TLS mode requires explicit opt-in through environment variables and should only be used in constrained environments.
