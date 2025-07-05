#!/usr/bin/env node
import { Command } from 'commander';
import { run } from '../src/index.js';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const pkg = require('../package.json');
const program = new Command();
program
  .name('autocommit')
  .version(pkg.version)
  .description(pkg.description)
  .option('--no-stage', 'skip git add .')
  .option('--dry-run', 'only print commit message, do not commit')
  .option('-c, --config <path>', 'path to config file')
  .option('--short', 'generate one-line summary only')
  .option('--verbose', 'print detailed logs')
  .parse(process.argv);

const options = program.opts();

(async () => {
  try {
    await run(options);
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
})();
