# readMD v2.1.1 → v2.2.2 事实卡

## Sources

- https://github.com/Natsummerance/readMD/compare/v2.1.1...main
- https://github.com/Natsummerance/readMD/blob/main/README.md
- https://github.com/Natsummerance/readMD/releases/tag/v2.2.0
- https://github.com/Natsummerance/readMD/releases/tag/v2.2.1

## Verified facts

- v2.2.0：AI schema v2、自定义连接 CRUD、API Key 不经接口明文回传；编辑工具栏、命令面板、公式选择器、图片编辑和预览停靠升级。
- v2.2.1：独立原生 macOS 发布线，区分 Intel 与 Apple Silicon。
- main 的 v2.2.2 准备提交：网页转 Markdown 使用 Trafilatura 双级抽取，静态内容不足时降级到 WebView2/WKWebView + Mozilla Readability；支持完整页面、同站最多 10 页和可选图片本地化。
- README 当前同时列出 Windows 安装版/便携版与 macOS 两种架构包。

## Release-state rule

调用 GitHub Release API 或页面确认目标 tag。目标 Release 不存在时，使用「v2.2.2 更新线」「主分支已准备」等表述，不使用「v2.2.2 已发布」。
