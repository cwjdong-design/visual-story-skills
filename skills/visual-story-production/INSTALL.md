# 独立技能包使用说明

导入整个 visual-story-production 文件夹，不要只复制 SKILL.md。按你的 Agent 支持的方式安装；没有自动导入功能时，让 Agent 显式读取 SKILL.md 及所链接的文件。

入口与详细规则为中文。开始示例：“使用 visual-story-production，把我的故事规划成3格漫画，先完成设定和分镜，不提交生成。”

没有任何作者服务依赖；画布、账号、模型与媒体工具由用户自行提供。工具不足时只交付能真实完成的文件和计划。复制 assets/project-template 到私人工作目录后开始，不覆盖原项目。

可选校验：Python 3.10+，运行 `python scripts/validate_project.py <项目目录>`。不需要第三方库，不调用网络。结构通过不等于剧情、媒体或用户确认通过。

本版短剧是规划扩展，未通过真实视频/剪辑全流程验证。不附已验证的商业平台适配器。

MIT 许可证见 LICENSE.txt；第三方素材权利不包含在内。
