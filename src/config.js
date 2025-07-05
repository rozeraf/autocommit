import fs from 'fs';
import { cosmiconfig } from 'cosmiconfig';
import dotenv from 'dotenv';

export async function loadConfig(customPath) {
  // load .env if exists
  if (fs.existsSync('.env')) {
    dotenv.config();
  }
  const explorer = cosmiconfig('autocommit');
  const rc = customPath
    ? await explorer.load(customPath)
    : await explorer.search();

  const env = process.env;
  return {
    prefix: env.AUTOCOMMIT_PREFIX || rc?.config?.prefix || 'Auto-commit:',
    maxSummaryLength: rc?.config?.maxSummaryLength || 250,
    includeDiffStat:
      (env.AUTOCOMMIT_INCLUDE_DIFF_STAT ??
        String(rc?.config?.includeDiffStat)) === 'true',
    includeKeywords: rc?.config?.includeKeywords ?? true,
    keywordsRegex:
      rc?.config?.keywordsRegex ||
      'function |class |const |let |var |def |type ',
    shortTemplate:
      env.AUTOCOMMIT_SHORT_TEMPLATE ||
      rc?.config?.shortTemplate ||
      '{files}{count,?+: +{count} more}',
    longTemplate:
      rc?.config?.longTemplate || '{prefix} {summary}\n\nChanges:\n{stat}',
  };
}
