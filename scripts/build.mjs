#!/usr/bin/env node
/**
 * `npm run build` is the gate wired into the Neon workflow.
 *
 * TrackIt has no JavaScript bundling step (the front end is plain HTML/CSS/JS
 * served by Flask), so this gate verifies the two things that can actually
 * break:
 *
 *   1. the Neon service policy declared in neon.ts, compiled and planned by the
 *      Neon CLI against the linked branch; and
 *   2. the Flask application's test suite.
 *
 * Both must pass for the build to succeed.
 */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

function run(label, command, args) {
  process.stdout.write(`\n▶ ${label}\n`);
  const result = spawnSync(command, args, { stdio: "inherit" });
  if (result.error) {
    console.error(`\n✗ ${label}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) {
    console.error(`\n✗ ${label} failed (exit ${result.status})`);
    process.exit(result.status ?? 1);
  }
  console.log(`✓ ${label}`);
}

run("Neon config plan", "neon", ["config", "plan"]);

const venvPython =
  process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python";
const python = existsSync(venvPython) ? venvPython : "python3";

run("Flask test suite", python, ["-m", "unittest", "discover"]);
