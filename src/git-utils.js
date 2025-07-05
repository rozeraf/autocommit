import { execa } from 'execa';

export async function stageAll() {
  await execa('git', ['add', '.']);
}

export async function getFileChanges() {
  const { stdout } = await execa('git', ['diff', '--cached', '--name-status']);
  return stdout
    .trim()
    .split('\n')
    .map((line) => line.split(/\s+/));
}

export async function getDiffStat() {
  const { stdout } = await execa('git', ['diff', '--cached', '--stat']);
  return stdout;
}

export async function commit(message) {
  await execa('git', ['commit', '-m', message]);
}
