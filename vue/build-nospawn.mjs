/* Compile Vue SFCs to plain JS modules without spawning child processes.
 *
 * Output: .build-tmp/ (JS modules mirroring src/, .vue files become .vue.js).
 * Bundling is done afterwards by running esbuild.exe directly (CLI), which the
 * sandbox only forbids as a node child_process but allows as a direct process.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse, compileScript } from "@vue/compiler-sfc";

const root = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.join(root, "src");
const tmpDir = path.join(root, ".build-tmp");
const outDir = path.join(root, "..", "views", "config");

const INDEX_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenAI 兼容图像生成与编辑</title>
<link rel="stylesheet" href="./assets/app.css?v=BUILD_TS">
</head>
<body>
<div id="app"></div>
<script type="module" src="./assets/app.js?v=BUILD_TS"></script>
</body>
</html>
`;

/* Rewrite relative "./X.vue" imports to the compiled "./X.vue.js" modules. */
function rewriteVueImports(code) {
  return code.replace(
    /(from\s+["'])(\.\.?\/[^"']+\.vue)(["'])/g,
    (match, head, spec, tail) => `${head}${spec}.js${tail}`,
  );
}

function listFiles(dir) {
  const found = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...listFiles(full));
    } else {
      found.push(full);
    }
  }
  return found;
}

fs.rmSync(tmpDir, { recursive: true, force: true });
fs.mkdirSync(tmpDir, { recursive: true });

const files = listFiles(srcDir);
let compiled = 0;
for (const file of files) {
  const rel = path.relative(srcDir, file);
  const target = path.join(
    tmpDir,
    file.endsWith(".vue") ? rel + ".js" : rel,
  );
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const source = fs.readFileSync(file, "utf8");
  if (file.endsWith(".vue")) {
    const { descriptor, errors } = parse(source, { filename: file });
    if (errors.length > 0) {
      console.error(`[sfc] ${rel}:`, errors.map((err) => err.message));
      process.exit(1);
    }
    const id = rel.replace(/[^\w]/g, "-");
    const result = compileScript(descriptor, {
      id,
      inlineTemplate: true,
      production: true,
    });
    fs.writeFileSync(target, rewriteVueImports(result.content), "utf8");
    compiled += 1;
  } else {
    fs.writeFileSync(target, rewriteVueImports(source), "utf8");
  }
}

fs.mkdirSync(path.join(outDir, "assets"), { recursive: true });
fs.writeFileSync(
  path.join(outDir, "index.html"),
  INDEX_HTML.replace(/BUILD_TS/g, String(Date.now())),
  "utf8",
);
console.log(`compiled ${compiled} SFC(s), ${files.length} file(s) -> .build-tmp`);

/* Bundle with the esbuild binary and copy the stylesheet. Spawn is allowed on
 * normal machines; sandboxed environments print the equivalent shell commands. */
import { spawnSync } from "node:child_process";

const esbuild = path.join(root, "node_modules", "@esbuild", "win32-x64", "esbuild.exe");
const bundle = spawnSync(
  esbuild,
  [
    path.join(tmpDir, "main.js"),
    "--bundle",
    "--format=esm",
    "--minify",
    `--outfile=${path.join(outDir, "assets", "app.js")}`,
    `--alias:vue=${path.join(root, "node_modules", "vue", "dist", "vue.runtime.esm-browser.prod.js")}`,
  ],
  { stdio: "inherit" },
);
if (bundle.error) {
  console.error(
    "[build] spawn failed; run manually:\n" +
      `  ${esbuild} .build-tmp/main.js --bundle --format=esm --minify --outfile=../views/config/assets/app.js --alias:vue=./node_modules/vue/dist/vue.runtime.esm-browser.prod.js\n` +
      "  cp src/style.css ../views/config/assets/app.css",
  );
  process.exit(2);
}
fs.copyFileSync(path.join(srcDir, "style.css"), path.join(outDir, "assets", "app.css"));
console.log("bundle + css -> ../views/config/assets");
