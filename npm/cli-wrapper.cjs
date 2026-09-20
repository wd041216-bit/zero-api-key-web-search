#!/usr/bin/env node
"use strict";

const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const PYTHON_MODULE = "zero_api_key_web_search";
const PYPI_PACKAGE = "zero-api-key-web-search";
const PYPI_VERSION = "21.0.0";

const COMMANDS = {
  "zero-search": "zero_api_key_web_search.search_web",
  "zero-context": "zero_api_key_web_search.context",
  "zero-browse": "zero_api_key_web_search.browse_page",
  "zero-verify": "zero_api_key_web_search.verify_claim",
  "zero-report": "zero_api_key_web_search.evidence_report",
  "zero-mcp": "zero_api_key_web_search.mcp_server"
};

const ALIASES = {
  search: "zero-search",
  context: "zero-context",
  browse: "zero-browse",
  verify: "zero-verify",
  report: "zero-report",
  mcp: "zero-mcp"
};

function help() {
  return [
    "Zero-API-Key Web Search npm wrapper",
    "",
    "Usage:",
    "  npx zero-api-key-web-search <command> [args...]",
    "  zero-search [args...]",
    "  zero-context [args...]",
    "  zero-browse [args...]",
    "  zero-verify [args...]",
    "  zero-report [args...]",
    "  zero-mcp",
    "",
    "Commands:",
    "  zero-search    Search the web",
    "  zero-context   Build LLM-ready context",
    "  zero-browse    Extract readable page text",
    "  zero-verify    Verify a factual claim",
    "  zero-report    Generate an evidence report",
    "  zero-mcp       Start the MCP server",
    "",
    "Python dependency:",
    `  python -m pip install ${PYPI_PACKAGE}==${PYPI_VERSION}`,
    "",
    "Examples:",
    "  npx zero-api-key-web-search zero-context \"Python release\" --goggles docs-first",
    "  zero-search \"AI regulation news\" --type news --timelimit w",
    "  zero-mcp"
  ].join("\n");
}

function findPython() {
  for (const candidate of ["python3", "python"]) {
    const result = spawnSync(candidate, ["--version"], { stdio: "ignore" });
    if (result.status === 0) {
      return candidate;
    }
  }
  return null;
}

function pythonHasPackage(python) {
  const result = spawnSync(
    python,
    ["-c", `import ${PYTHON_MODULE}`],
    { stdio: "ignore" }
  );
  return result.status === 0;
}

function printInstallHint(python) {
  console.error(`Could not import Python package '${PYTHON_MODULE}'.`);
  console.error("");
  console.error("Install the Python runtime package first:");
  console.error(`  ${python} -m pip install ${PYPI_PACKAGE}==${PYPI_VERSION}`);
  console.error("");
  console.error("This npm package is a thin npx/MCP wrapper and does not auto-install Python dependencies.");
}

function resolveInvocation(argv) {
  const invoked = path.basename(argv[1] || "").replace(/\.js$/, "");
  const args = argv.slice(2);

  if (invoked === "zero-api-key-web-search") {
    const requested = args[0];
    if (!requested || requested === "--help" || requested === "-h") {
      return { help: true };
    }
    const normalized = ALIASES[requested] || requested;
    if (!COMMANDS[normalized]) {
      return { error: `Unknown command '${requested}'.\n\n${help()}` };
    }
    return { command: normalized, args: args.slice(1) };
  }

  if (!COMMANDS[invoked]) {
    return { error: `Unknown wrapper invocation '${invoked}'.\n\n${help()}` };
  }
  return { command: invoked, args };
}

function main() {
  const resolved = resolveInvocation(process.argv);
  if (resolved.help) {
    console.log(help());
    process.exit(0);
  }
  if (resolved.error) {
    console.error(resolved.error);
    process.exit(2);
  }

  const python = findPython();
  if (!python) {
    console.error("Could not find python3 or python on PATH.");
    console.error(`Install Python 3.10+ and then run: python -m pip install ${PYPI_PACKAGE}==${PYPI_VERSION}`);
    process.exit(127);
  }

  if (!pythonHasPackage(python)) {
    printInstallHint(python);
    process.exit(1);
  }

  const child = spawn(
    python,
    ["-m", COMMANDS[resolved.command], ...resolved.args],
    { stdio: "inherit" }
  );

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
    }
    process.exit(code ?? 1);
  });
  child.on("error", (error) => {
    console.error(error.message);
    process.exit(1);
  });
}

main();
