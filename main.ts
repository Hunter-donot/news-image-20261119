// Entry for the make.fun bounty "Post a GTA 6 meme on X" (gta6-meme-x-01).
//
// The meme itself is posted on X; this program's only job is to hand the
// grader the post's address. It copies POST.json from the repository root
// into the output directory, byte for byte, and nothing else.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const botDir = process.env.MAKEFUN_BOT_DIR ?? "/bot";
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const src = join(botDir, "POST.json");
const dst = join(outDir, "POST.json");

if (!existsSync(src)) {
  console.error(`POST.json not found at ${src}`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });

try {
  copyFileSync(src, dst);
} catch (err) {
  console.error(`failed to copy POST.json to ${dst}: ${err}`);
  process.exit(1);
}

console.log(`wrote ${dst}`);
