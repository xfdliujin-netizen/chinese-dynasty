# 历史长卷 · 原生自用包（鸿蒙 + iOS）

自用侧载，不进任何应用商店。技术形态：原生壳 + 内置 WebView 加载本地 web 资源。

## 目录结构

```
apps/
├── scripts/
│   ├── prepare-web.py      # 一键打包：web -> web包 -> 鸿蒙/iOS 资源目录
│   └── native-shim.js      # 原生壳适配层（视图上报 / 返回键 / 存储兜底）
├── web/                    # 打包产物（勿手改，脚本生成）
├── harmony/                # 纯血鸿蒙工程（DevEco 直接打开）
└── ios/                    # iOS 工程（XcodeGen，Mac 上生成 xcodeproj）
```

## 日常更新流程（改完 web 之后）

```bash
python apps/scripts/prepare-web.py
```

这一条命令会：复制 web 文件、替换 Google Fonts 为本地书法体、注入 native-shim、
同步到鸿蒙 rawfile 与 iOS Resources。之后重新 Run 即可。

注意：`apps/web/`、`apps/harmony/.../rawfile/`、`apps/ios/.../Resources/web/` 都是生成物，
不要直接改，改了会被下一次打包覆盖。

---

## 鸿蒙安装（Windows 即可全流程）

1. 装 DevEco Studio（华为开发者官网，免费），首次启动会自动下载 SDK。
2. File → Open，打开 `apps/harmony`。
   - 若提示 hvigor 版本不匹配，点「升级」即可（工程按 5.0.0 模板写，新版本自动升）。
3. 华为开发者账号：AppGallery Connect 实名认证（个人即可，免费）。
4. 自动签名：File → Project Structure → Signing Configs →
   勾选 Automatically generate signature → 登录账号 → 完成。
5. 手机：设置 → 关于手机 → 连点版本号开启开发者模式；
   设置 → 开发者选项 → 打开 USB 调试。
6. USB 连接手机（选「传输文件」），手机上允许调试授权。
7. DevEco 右上角选中你的设备，点 Run ▶。应用「历史长卷」即装到手机。
8. 证书到期后（调试签名约一年），重新点一次 Run 即自动续签。

### 已知风险点

- **史图 iframe**：rawfile 协议下 iframe 加载同目录 html 是唯一有技术风险的环节。
  Index.ets 里内置了 25 秒自检，若失败会弹出底部提示条「史图未就绪」。
  长卷不受影响。若遇到，把 `apps/harmony/.../pages/Index.ets` 中注释里
  「内联方案」一节放开，或联系我把地图页并入主文档。
- **字体**：正文用系统黑体（iOS 苹方 / 鸿蒙 HarmonyOS Sans），与 web 版一致；
  印章书法体已子集化内置（9.5KB）。

---

## iOS 安装（需要一台 Mac，仅最后一步编译）

### 生成工程（Mac 上）

```bash
brew install xcodegen
cd apps/ios
xcodegen generate     # 生成 HistoryScroll.xcodeproj
open HistoryScroll.xcodeproj
```

### 方式一：免费 Apple ID（0 元，7 天有效期）

1. Xcode → Settings → Accounts → 用 Apple ID 登录。
2. 选中 HistoryScroll target → Signing & Capabilities → Team 选你的 Personal Team。
3. iPhone 连 Mac → 手机上点「信任」→ Xcode 顶部选中设备 → Run ▶。
4. 手机：设置 → 通用 → VPN 与设备管理 → 信任你的开发者证书。
5. 7 天后 App 打不开，重新插 Mac 点一次 Run 即可。免费账号最多同时 3 个 App。

### 方式二：Apple Developer 会员（$99/年，一年免维护）

同上，只是 Team 选付费账号；签名证书一年有效，适合长期自用。

### 已知设计点

- web 资源通过自定义 `app://local/` 协议提供（AppSchemeHandler.swift），
  iframe 同源、localStorage、@font-face 行为与浏览器一致——这是刻意避开
  WKWebView 对 file:// 的诸多限制。
- 若未来 web 引入了新的资源类型（新扩展名），在 AppSchemeHandler.swift 的
  `mime(for:)` 里补一行映射即可。

---

## 常见问题

| 现象 | 处理 |
|---|---|
| 鸿蒙史图空白，长卷正常 | 见上文「史图 iframe」；自检提示条会给出原因码 |
| iOS 字体变宋体/楷体 | 检查 seal.woff2 是否在包内，AppSchemeHandler 的 woff2 MIME |
| 鸿蒙侧滑返回直接退出 | 正常现象仅限长卷页；史图页会先退回长卷 |
| 改了 web 没生效 | 先跑 prepare-web.py，再重新 Run；生成物不会自动同步 |
| 图标显示为默认 | 确认 app_icon.png 在 AppScope 与 entry 两处 media 里都存在 |
