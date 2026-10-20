# Visual Story Skills · 视觉叙事制作技能

**把故事变成能制作、能检查、能交接的漫画与 AI 短剧项目。**

给你自己的 Agent 使用，在你自己的画布和生成平台工作。无需原工作台、服务端、数据库、指定模型或统一账号；本仓库不会代理模型调用，也不收集项目数据。

**v0.1.0：漫画制作方法已提取，短剧是明确标注的扩展规则。** 包含文件级校验和离线回归测试；未宣称通过独立 Agent 全流程实测，也未验证任何商业平台的真实生成、剪辑效果。

## 30 秒了解

```text
故事诊断 → 制作设定 → 分镜/镜头表 → 参考资产与画布生成 → 审核和局部返工
                         ↖ 项目文件保存版本、依据、进度 ↗
```

不是“你是一位导演”的角色提示词。它告诉 Agent：输入缺什么、此刻做什么、产出什么、怎么查错、修改会影响哪里、什么时候应停下来。

## 安装与开始

1. 下载本仓库，或克隆：
   ```sh
   git clone https://github.com/cwjdong-design/visual-story-skills.git
   ```
2. 把 **整个** `skills/visual-story-production/` 文件夹交给支持目录型 Skill 的 Agent，按该 Agent 的方式导入。不要只复制 `SKILL.md`，否则阶段规则、模板和工具会丢失。
3. 如果 Agent 没有 Skill 导入功能，让它读取 `skills/visual-story-production/SKILL.md`，并允许它读取同目录引用文件。这是手动加载，不保证每个产品都有自动发现能力。
4. 在自己的工作目录创建项目，不要把私人项目存进公开仓库。你可以说：

   > 使用 visual-story-production，把这个故事做成 6 格漫画。先给我故事诊断、制作设定和分镜，不调用生成平台。请把资料保存成可交接的项目。

   或：

   > 使用 visual-story-production，把这个故事规划为一集约 30 秒的竖屏短剧。先提交镜头表和声音设计，生成与发布前等我确认。

   接续工作：

   > 读取我的项目文件，找出当前有效版本和未解决问题。从上次停止的位置继续；不要自动重新生成已有素材。

这里不绑定某一家 Agent。能读写文件的 Agent 可运行制作资料流程；操作画布还需要用户提供可用的浏览器、连接器或平台工具。**安装 Skill 本身不会赋予工具、账号、生成额度或平台权限。**

## 包含什么

| 文件 | 用途 |
| --- | --- |
| `SKILL.md` | 识别阶段、路由规则、控制确认与交接 |
| `references/01-story.md` | 完整性、因果、钩子、共鸣和结尾 |
| `references/02-production.md` | 身份/造型/状态分离、事实依据、画内人物 |
| `references/03-storyboard.md` | 总纲后细化、单格瞬间、文字容量和连续性 |
| `references/04-production-tools.md` | 参考图用途、画布交接、异步结果和重试 |
| `references/05-review.md` | 审核、修改影响、项目接续 |
| `references/short-drama.md` | 时长、动作、声音和剪辑扩展 |
| `references/project-format.md` | 独立项目文件约定与字段解释 |
| `assets/project-template/` | 可复制的空项目模板 |
| `scripts/validate_project.py` | Python 标准库离线检查，不调用网络或模型 |
| `examples/` | 同一原创小故事的漫画/短剧规划示例；没有伪造生成结果 |

详见 [使用指南](docs/USAGE.md)、[画布适配模板](docs/platform-adapter-template.md)、[方法提取与边界](docs/EXTRACTION.md)。

## 画布与平台

技能描述制作意图，不猜测平台按钮、节点名、模型能力或接口。首次使用时，Agent 应先发现用户现有工具，写下本项目的平台能力；再把“角色参考 + 场景参考 → 镜头生成”映射到实际操作。**本版不附带已验证的平台专用适配器。**

没有平台工具时仍可交付故事、设定、镜头表和可复制提示词；不能声称已经操作画布、生成素材或剪辑成片。

## 本地检查

需要 Python 3.10+；制作规则本身不依赖 Python。

```sh
python skills/visual-story-production/scripts/validate_project.py examples/comic-umbrella
python skills/visual-story-production/scripts/validate_project.py examples/short-drama-umbrella
python -m unittest discover -s tests -v
python tools/check_package.py
python tools/build_release.py
```

校验通过只表示可检查的结构和引用通过，不代表剧情好、画面正确、用户已批准或成片已完成。

## 分享与贡献

- 分享仓库链接或 Releases 中的独立技能压缩包，不要分享个人项目、账号或浏览器会话。
- 欢迎补充通用制作规则、原创示例和有证据的平台适配说明。贡献方法见 [CONTRIBUTING.md](CONTRIBUTING.md)。
- [MIT License](LICENSE)：可使用、修改和再分发技能内容；不授予第三方素材、人物肖像、商标或平台服务的权利。

[English overview](README.en.md) · [更新记录](CHANGELOG.md) · [安全说明](SECURITY.md)
