# Universal Bilingual Reader

在线访问：[https://glyuan419.github.io/universal_bilingual_reader/](https://www.google.com/search?q=https://glyuan419.github.io/universal_bilingual_reader/)

**Universal Bilingual Reader** 是一个离线优先的通用中英双语阅读器器，支持以 PWA 形式安装为 Android 应用。

## 仓库目录结构

本仓库**外壳与内容分离**，日常需维护 3 个位置：

```
universal_bilingual_reader/
├── .github/workflows/
│   └── build-index.yml                 # 自动化构建与部署流水线
├── updates/
│   └── ubr-vX.Y.Z-gh-pages-kit.zip     # 站点外壳更新包
└── library/
    ├── 2611.07578v1.zip                 # 双语资源包（.zip，内含 doc.json + assets/，推荐）
    └── some-doc/                        # 或双语资源包解压后的文件夹
```

## GitHub Pages 自动化工作逻辑

每次向 `main` 分支推送提交（或手动在 Actions 页面触发）时，`.github/workflows/build-index.yml` 会执行 **Clean-Room Build**，在云端临时目录 `_site/` 中拼装出最终站点并发布：

```
push 到 main
   │
   ├─ 1. Clean-Room Build 初始化 _site/（空目录起步）
   ├─ 2. 从仓库中的 updates/ 自动选取语义版本号（vX.Y.Z）最高的站点外壳 .zip 解包进 _site/
   │     （内含 Atlas 单页 index.html、manifest.webmanifest、sw.js、图标及 scripts/build_index.py）
   ├─ 3. 将仓库中的 library/（及可选自定义域名文件 CNAME）独立拷入 _site/
   ├─ 4. 在 _site/ 内执行 scripts/build_index.py，扫描 library/ 自动生成最新 catalog.json
   ├─ 5. 用本次 commit 前 7 位哈希刷新 _site/sw.js 缓存版本，确保手机 PWA 自动更新
   └─ 6. 上传 _site/ 产物并部署至 GitHub Pages
```

### 核心设计原则

* **外壳与内容解耦**：`updates/*.zip` 仅包含纯净应用外壳；线上书架严格以仓库 `library/` 里的实际文件为准。
* **单页共享引擎（Atlas）**：全站仅使用一份 `index.html`（无 `?doc=` 时展示书架首页，点击条目零刷新加载 `?doc=library/...`），升级引擎后所有历史文献自动生效。
* **新版舍弃文件零残留**：由于 `_site/` 每次从空目录由最新外壳包重建，新版不再包含的旧文件会自动从线上消失。

## 日常维护流程

### 1. 新增或删除文献

* **新增**：将符合协议的 `.zip` 资源包（或解压后的文件夹）上传至 `library/` 并提交；
* **删除**：直接删除 `library/` 中的对应文件并提交。约 1–2 分钟后 Actions 完成重新索引与部署，书架自动同步。

### 2. 升级网站阅读器外壳

* 将新版纯净外壳包 `ubr-vX.Y.Z-gh-pages-kit.zip` 上传至 `updates/`（替换旧包或直接新增，流水线会自动挑版本号最高的包）并提交即可；
* 若只更新单页阅读器，也可在清空 `updates/` 中的 `.zip` 后直接放入导出的 Atlas `.html`。

### 3. 首次启用 Pages 配置（一次性）

1. 进入仓库 **Settings → Pages → Build and deployment → Source**；
2. 将来源切换为 **GitHub Actions**；
3. 如需在 Android 手机作为独立 App 使用，部署完成后用 Chrome 打开站点链接，点右上角菜单 **「安装并创建快捷方式」** 即可。
