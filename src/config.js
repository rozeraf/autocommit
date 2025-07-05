import { cosmiconfig } from 'cosmiconfig';

const explorer = cosmiconfig('autocommit');
export async function loadConfig(customPath) {
  const result = customPath
    ? await explorer.load(customPath)
    : await explorer.search();
  return {
    prefix: 'Auto-commit:',
    maxSummaryLength: 250,
    includeDiffStat: true,
    includeKeywords: true,
    keywordsRegex: 'function |class |const |let |var |def |type ',
    ...result?.config,
  };
}
