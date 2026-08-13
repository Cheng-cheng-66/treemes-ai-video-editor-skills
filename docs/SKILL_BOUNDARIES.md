# Skill 边界

## core

允许：

- 路径和配置
- 外部进程
- 媒体探测
- QC 三态结果
- 任务/日志基础
- Skill 注册
- Release 状态

禁止：

- `MES 日记` 标题坐标
- 工厂 B-roll 匹配规则
- 客户案例叙事和隐私判断

## video_diary

拥有封面、正文顶部模板、逐字字幕、安全区、停顿策略、自然画面处理和视频日记回归规则。当前为启用的 Beta Skill。

## factory_shoot

未来拥有设备/产线/工人/看板/三色灯/MES 画面识别、素材质量、空镜分类、B-roll 匹配、工业节奏、候选镜头人工确认。当前 manifest 为 `planned + disabled`；现有 `work/factory_demo` 是历史原型，不是生产入口。

## case_study

拥有访谈转写、同步区、停顿、高价值观点、背景/问题/方案/成果结构、长转短、事实确认、隐私授权和强制人工审核。当前 manifest 为启用的 Beta 分析入口，正式渲染仍等待首条案例验收。

## 强制规则

- 场景 Skill 只能导入 `core` 或自己的内部模块。
- Skill 不得读写其他 Skill 的内部状态。
- 共用能力只有在第二个真实场景需要且测试通过后才上提 Core。
- 新场景未满足门禁时必须保持 `enabled: false`。
