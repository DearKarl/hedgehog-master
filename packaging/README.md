# Packaging / 封装交付

Hedgehog Master keeps generated delivery artifacts out of Git. The tracked scripts in this directory are the reproducible source of every local package.

Hedgehog Master 不把生成后的交付文件提交进 Git。此目录中的脚本是本地应用和发布包的可复现构建来源。

## macOS development launcher / macOS 开发启动器

```bash
packaging/macos/build_app.sh \
  --output "$HOME/Desktop/Hedgehog Master.app" \
  --linked-root "$PWD"
```

The linked build uses the current checkout as its source, installs a clean runtime copy into `~/Library/Application Support/Hedgehog Master`, and records the base Python interpreter for local evaluation. Projects remain in a version-independent directory. The finished app starts the service when necessary and opens the default browser without reading the Desktop source tree.

关联构建以当前仓库为源码，把干净运行副本安装到 `~/Library/Application Support/Hedgehog Master`，并记录本机基础 Python 解释器用于测试。项目保存在版本无关的目录中。生成后的 App 无需读取桌面源码即可按需启动服务并打开默认浏览器。

## Portable evaluation package / 可移交测试包

Build Diagram IR first so the package contains the compiled CLI, then build the release:

先构建 Diagram IR，确保发布包包含编译后的 CLI，然后生成交付包：

```bash
pnpm -C packages/diagram-ir build
packaging/release/build_release.sh
```

The generated directory and ZIP are written under `dist/` and contain:

- `Hedgehog Master.app`: HM launcher
- `hedgehog_master/`: runtime source without Git history, caches, virtual environments, or large examples
- `setup.command`: first-run Python setup
- `START_HERE.md`: bilingual handoff instructions
- `MANIFEST.sha256`: file integrity manifest

The current beta uses an ad-hoc macOS signature and is not notarized.
