import { stageAll, getFileChanges, getDiffStat, commit } from './git-utils.js';
import { loadConfig } from './config.js';
import chalk from 'chalk';
import fs from 'fs';

export async function run(opts) {
  const cfg = await loadConfig(opts.config);

  if (opts.stage) await stageAll();
  const changes = await getFileChanges();
  const diffStat = cfg.includeDiffStat ? await getDiffStat() : '';

  let summary = '';
  for (const [status, file] of changes) {
    let type;
    switch (status) {
      case 'A':
        type = 'added';
        break;
      case 'M':
        type = 'modified';
        break;
      case 'D':
        type = 'deleted';
        break;
      case 'R':
        type = 'renamed';
        break;
      default:
        type = 'updated';
    }
    let keywords = '';
    if (cfg.includeKeywords && fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const matches = [...content.matchAll(new RegExp(cfg.keywordsRegex, 'gi'))]
        .slice(0, 3)
        .map((m) => m[0].trim());
      if (matches.length) keywords = `: ${matches.join('; ')}`;
    }
    summary += `${file} (${type})${keywords} | `;
  }
  summary = summary.slice(0, cfg.maxSummaryLength);

  const fileNames = changes.map(([_, file]) => file);
  const shortSummary = `${fileNames.slice(0, 3).join(', ')}${
    fileNames.length > 3 ? ` +${fileNames.length - 3} more` : ''
  }`;

  const header = opts.short
    ? `${cfg.prefix} ${shortSummary}`
    : `${cfg.prefix} ${summary}`;

  const message = opts.short ? header : `${header}\n\nChanges:\n${diffStat}`;

  console.log(chalk.green('Generated commit message:'));
  console.log(message);

  if (!opts.dryRun) {
    await commit(message);
    console.log(chalk.blue('Commit completed.'));
  }
}
