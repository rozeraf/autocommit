import fs from 'fs';
import chalk from 'chalk';
import { stageAll, getFileChanges, getDiffStat, commit } from './git-utils.js';
import { loadConfig } from './config.js';

function applyTemplate(template, data) {
  return template
    .replace('{prefix}', data.prefix)
    .replace('{summary}', data.summary)
    .replace('{stat}', data.stat)
    .replace('{files}', data.files.join(', '))
    .replace('{count}', String(data.count));
}

export async function run(opts) {
  const cfg = await loadConfig(opts.config);
  if (opts.stage) await stageAll();

  const changes = await getFileChanges();
  const diffStat = cfg.includeDiffStat ? await getDiffStat() : '';

  const summary = changes
    .map(([status, file]) => {
      const typeMap = {
        A: 'added',
        M: 'modified',
        D: 'deleted',
        R: 'renamed',
      };
      const type = typeMap[status] || 'updated';
      return `${file} (${type})`;
    })
    .join(' | ');

  const files = changes.map(([_, file]) => file);
  const count = files.length;

  // build message
  const data = { prefix: cfg.prefix, summary, stat: diffStat, files, count };
  const message = opts.short
    ? applyTemplate(cfg.shortTemplate, data)
    : applyTemplate(cfg.longTemplate, data);

  console.log(chalk.green('Generated commit message:'));
  console.log(message);

  if (!opts.dryRun) {
    await commit(message);
    console.log(chalk.blue('Commit completed.'));
  }
}
