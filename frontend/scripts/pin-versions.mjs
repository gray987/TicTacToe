// One-off helper: replace "latest" in package.json with ^<installed version>.
// Usage (after `npm install`):  node scripts/pin-versions.mjs  &&  npm install
// The final `npm install` refreshes package-lock.json so `npm ci` stays in sync.
import { existsSync, readFileSync, writeFileSync } from "node:fs";

const packageJsonUrl = new URL("../package.json", import.meta.url);
const pkg = JSON.parse(readFileSync(packageJsonUrl, "utf8"));
let pinned = 0;

for (const section of ["dependencies", "devDependencies"]) {
  for (const [name, range] of Object.entries(pkg[section] ?? {})) {
    if (range !== "latest") continue;
    const installedUrl = new URL(`../node_modules/${name}/package.json`, import.meta.url);
    if (!existsSync(installedUrl)) {
      console.error(`skipped ${name}: not installed (run npm install first)`);
      continue;
    }
    const { version } = JSON.parse(readFileSync(installedUrl, "utf8"));
    pkg[section][name] = `^${version}`;
    pinned += 1;
    console.log(`${name}: latest -> ^${version}`);
  }
}

writeFileSync(packageJsonUrl, JSON.stringify(pkg, null, 2) + "\n");
console.log(`pinned ${pinned} package(s)`);
