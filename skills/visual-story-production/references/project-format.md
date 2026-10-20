# 独立项目约定 · schemaVersion 1

这是本技能的轻量交换格式，不要求部署任何服务。JSON 使用 UTF-8。可在用户现有项目格式中做等价映射，不强迫迁移；若要使用内置校验器，则遵循以下结构。

## 文件

- `project.json`：schemaVersion、projectId、title、medium（comic/short-drama）、项目 revision、target、story/production/shots 三个文件引用与各自 revision/status。
- `story.md`：当前采用正文；历史稿保存在 `history/`，每次修改更新 story.revision。
- `production.json`：revision、storyRevision、style、phases、assets。
- `shots.json`：revision、storyRevision、productionRevision、shots、warnings。
- `runs.json`：records，保留实际生成尝试；空数组表示尚未提交，不代表失败。
- `progress.md`：决定、阻塞、已执行动作和下一步。
- `platform.md`：可选，本项目工具能力和未验证项。

JSON 文件路径使用相对于项目目录的路径；校验器禁止越界和绝对路径。`status` 为 draft / approved / stale。approved 必须有真实确认或用户已授予的代决权限，校验器无法替你证明这一点。

`target.panelCount` 仅漫画使用，`target.durationSeconds` 仅短剧使用；未知可为 null。`authorization` 记录 generationAllowed、publicationAllowed、maxAttemptsPerShot 与授权说明，默认都不允许外部执行。记录本身不是权限来源，必须与用户真实授权一致。

## 制作设定

`phases`：`{id, name, kind, sourceQuote}`，kind 是 story 或 depiction；sourceQuote 来自当前正文的连续原文。

`assets`：`{id, kind, name, visibility, description, sources, looks, states}`。
- kind 为 character / scene / prop；visibility 为 visible / text-only。
- 可视资产须有 look 和 state；文字资产的两者为空。
- `sources` 每项为 `{kind: "story", quote: "逐字原文"}` 或 `{kind: "design", note: "补充理由"}`。描述混有事实和设计时，具体字段与依据的对应关系写清，不因格式简化抹掉来源区分。
- look：`{id, description, sources}`。
- state：`{id, description, allowedLookIds, phaseIds, sources}`；phaseIds=[] 表示不额外限阶段。
- 可选画内人物绑定 `depictedSubjects`：`{assetId, lookId, stateId, depictionPhaseId}`；仅角色可作为画内人物。
- asset 上是常态绑定；state 上省略表示继承、[] 表示清空、非空数组完整替换。state 覆盖时必须同时有非空 contentChange 和 story 依据。

## 分镜

每镜必需：`id, phaseId, beat, sourceQuote, instant, assetIds, visualTargets, textBlocks`。
- phaseId 只选 story 阶段。
- visualTargets：`{assetId, lookId, stateId}`，只引用本镜现场可见且已经定义的目标。画内人物通过道具绑定引用，不自动加入现场。
- textBlocks：`{type, speakerId, text, carrier}`；type 为 dialogue/narration/caption/screen，speakerId 可为 null。carrier 写具体落点，如 bubble / overlay / phone-screen。
- 推荐补充 before、after、timeBridge、camera、composition；它们也是连续性审核依据。
- 短剧另有 durationSeconds（正数）、motion（连续动作描述）、audio（声音描述列表）；漫画不填视频时长。短剧对白仍放 textBlocks，不复制成另一份不同内容。

引用只对应当前故事和设定版本。上游改动后保留旧产物，标记 stale；校验器对陈旧依赖报告错误，提示不得将它当当前可执行版本。

## 任务记录

每项：`id, shotIds, shotRevision, platform, externalId, attempt, retryOf, state, outputPaths`。
- state：planned/submitted/running/succeeded/failed/unknown/cancelled。
- attempt 从1开始；retryOf 指向原尝试。历史记录不删除；输出路径在项目内，真实 succeeded 必须有 externalId 或实际存在的 outputPaths。
- 可选 `outputUrls` 记录用户可用且不含凭证的结果定位；仅有一个网址不能证明成功或质量通过。
- `shotRevision` 可以指向旧版，保留历史追溯；不能用旧结果证明新版镜头通过。
- unknown 不允许直接重试；先对账，更新原尝试的真实状态后再按授权重试。

## 脚本检查的范围

检查必需字段、路径边界、ID 唯一、版本一致、引文、造型/状态/阶段引用、数量/时长和部分重试记录。**不检查**真实批准、故事因果是否精彩、屏幕内容是否画对、平台是否收费、链接是否可用或媒体质量。详见运行结果中的警告。
