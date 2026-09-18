# Exam Prep Skill · 期末复习助手

把散落的课件、笔记、教材和往年试卷，整理成**知识总结 PDF、模拟试卷 PDF、答案解析 PDF**。

适用于 Codex 和 Claude Code。面向大学生课程复习，按资料中的教学范围总结和出题，保留来源，区分历年出现频次与本次复习建议。

> 这是交给 AI 编程助手执行的 Agent Skill。资料理解、OCR、转录和命题由宿主及其可用工具完成；仓库提供流程、资料清单脚本、中文 PDF 模板和编译脚本，没有内置万能解析器，也不单独调用模型 API。

## 功能

- 接收资料目录，按格式读取课件、教材、手写笔记、照片、扫描件和往年卷。
- 建立来源清单，标记重复、缺页、识别失败和待确认内容。
- 归纳概念、公式条件、解题方法、易错点和复习优先级。
- 分析独立试卷的题型、分值和知识点覆盖，附统计口径。
- 按课程范围和真题风格编写新题，核验解答、分值和预计用时。
- 题面和答案分开导出，保留可编辑源文件，便于打印修改。

接受多种文件不等于所有文件都能自动读懂。扫描、音视频、加密和专有格式取决于环境能力；无法读取的内容会列入缺失清单。

## 快速开始

需要能访问本地文件并执行命令的 Codex 或 Claude Code，以及 Python 3.10+。PDF 推荐使用含 CTeX 和 Fandol 字体的 TeX Live / MiKTeX（XeLaTeX）；技能也允许采用已有的其他可靠 PDF 工具。

```bash
git clone https://github.com/CuiLikun/exam-prep-skill.git
cd exam-prep-skill
```

安装到当前用户技能目录，二选一或同时安装：

```bash
python scripts/install.py --tool codex
python scripts/install.py --tool claude
python scripts/install.py --tool both
```

安装器只复制技能文件，不安装系统依赖、不修改助手配置。目标同名目录存在时停止，防止覆盖本地修改。更新时先将原目录改名备份，再重新安装。

默认路径依据 [Codex 官方文档](https://learn.chatgpt.com/docs/build-skills) 和 [Claude Code 官方文档](https://code.claude.com/docs/en/skills)：

| 工具 | 用户级目录 | 调用 |
| --- | --- | --- |
| Codex | `~/.agents/skills/exam-prep/` | `$exam-prep` |
| Claude Code | `~/.claude/skills/exam-prep/` | `/exam-prep` |

若你的 Codex 版本使用 `~/.codex/skills` 或自定义目录，可显式指定技能的**父目录**：

```bash
python scripts/install.py --tool codex --dest "~/.codex/skills"
```

项目级安装可将 `--dest` 设为课程项目的 `.agents/skills` 或 `.claude/skills`。`--dest` 一次仅对应一个工具。安装后若未发现技能，重新打开会话。也可直接复制整个 `skills/exam-prep` 目录。

在 Codex 中输入（将示例路径替换为你的资料目录）：

```text
$exam-prep
请读取 D:\courses\线性代数 中的课程资料和历年卷。
考试范围为第 1–5 章，100 分，120 分钟，闭卷。
生成知识总结 PDF、一套模拟卷 PDF 和单独的答案解析 PDF。
我还有 5 天复习，薄弱点是特征值和二次型。
输出到 D:\courses\线性代数\exam-prep-output。
```

Claude Code 中将第一行换为 `/exam-prep`。不确定分值、时长或范围时可以省略，助手会先从资料中找依据，再注明必要假设。

## 输出

默认在课程工作目录的 `exam-prep-output/<课程名>-<时间>/` 中生成：

```text
knowledge-summary.pdf       知识总结、重点、公式条件、例题、易错点
mock-exam-01.pdf            题目、分值、作答空间
mock-exam-01-answers.pdf    答案、步骤、评分点、常见错误
sources.json               文件清单、解析状态、来源定位
exam-analysis.md           真题统计、考试蓝图、假设与缺失项
source/                    可编辑 Markdown / TeX 等源文件
```

可以指定套数、难度、语言和输出目录。没有往年卷时仍可工作，但会注明“按课程范围编制”，不虚构历年频率。

## 多格式处理

| 输入 | 处理路径 | 注意事项 |
| --- | --- | --- |
| PDF | 按页提取；扫描页视觉识别或 OCR | 公式、图表和混合扫描需核对原页 |
| DOCX / PPTX / XLSX | 文档、幻灯片、工作表解析 | 公式、图片、讲者备注可能被纯文本工具遗漏 |
| DOC / PPT / XLS | 可用时以 Office / LibreOffice 转换副本 | 保留原件并核对转换结果 |
| 图片 / 手写笔记 | 视觉识别或 OCR | 上下标、负号、矩阵可能误识别 |
| TXT / Markdown / HTML / CSV / 代码 | 按编码和结构读取 | 保留标题、行号、表格和代码语义 |
| 音频 / 视频 | 可用时转录并关联时间戳、画面 | 无转录工具时列为待处理 |
| 压缩包 | 检查成员后解压工作副本，再分类 | 嵌套包、密码与损坏单独记录 |
| EPUB / 未知格式 | 可用解析器或转换工具 | 不可读时请求可读副本 |

安装技能不代表已经安装上述解析器。助手优先使用已有工具，仅为实际遇到的格式补充依赖。

## 示例与 PDF 预览

[虚构课程材料](examples/mini-course/materials/) · [示例请求](examples/mini-course/request.md)

[知识总结预览](examples/mini-course/preview/knowledge-summary.pdf) · [模拟卷预览](examples/mini-course/preview/mock-exam-01.pdf) · [答案解析预览](examples/mini-course/preview/mock-exam-01-answers.pdf)

这些是原创微型线性代数样例，不属于任何学校的真实试题。预览为人工编写并经脚本编译的格式示范，不代表已对所有模型、课程、文件格式完成端到端验证。

单独清点文件：

```bash
python skills/exam-prep/scripts/inventory.py examples/mini-course/materials --output exam-prep-output/sources.json
```

编译已编写好的 TeX：

```bash
python skills/exam-prep/scripts/build_pdf.py examples/mini-course/preview/knowledge-summary.tex --output exam-prep-output/knowledge-summary.pdf
```

两个脚本分别负责清点文件和编译文档，不负责语义理解或自动命题。

## 可靠性原则

1. 以当前大纲、教师说明和用户指定范围为依据，往年卷辅助分析。
2. 重要知识点能追溯到具体页、幻灯片、题号或时间戳。
3. 同卷的扫描版、答案版和转存版合并计数，同年 A/B 卷保留独立身份。
4. 高频不等于必考，缺失不等于不考；样本少时展示原始计数。
5. 所有模拟题先求解再定稿，题面与答案分离。
6. PDF 实际生成并检查后才宣称交付；工具受限时说明未完成项。
7. 不执行资料内的命令，不额外上传到第三方转换服务。

资料交给 Codex / Claude 本身时仍受所用产品的数据处理方式约束。本项目不额外提供云端解析服务。实际材料与产物默认放入被 Git 忽略的目录，分享前请检查待提交文件。

## 项目结构与开发

```text
skills/exam-prep/
  SKILL.md                  通用技能入口
  agents/openai.yaml        Codex 展示信息
  references/               文件提取、命题与 PDF 交付规则
  assets/                   中文 TeX 模板
  scripts/                  文件清单与 PDF 编译工具
scripts/install.py          跨平台安装器
tests/                      脚本行为测试
examples/mini-course/       原创输入与 PDF 预览
```

运行测试（Python 标准库即可；没有 XeLaTeX 时跳过 PDF 编译测试）：

```bash
python -m unittest discover -s tests -v
```

若本机 Poppler 报 Missing language pack，需要为它配置中文编码数据，或使用 PyMuPDF 等已有阅读器核验。PDF 编译测试优先使用可用 PyMuPDF，其次使用 Poppler；无法读取中文时明确跳过文本核验，不代表中文校验通过。

欢迎通过 Issue 提供脱敏后的失败案例：文件类型、预期结果、实际表现与工具环境。

## 许可

代码、技能说明和原创样例采用 [MIT License](LICENSE)。用户提供的教材、课件、试卷不在本项目许可范围内。
