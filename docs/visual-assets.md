# 视觉素材与生成记录

## README 封面

- 文件：`assets/readme/hero.png`。
- 用途：仓库首页的概念插图，展示课程资料汇成三类复习材料。
- 方式：通过内置 `image_gen` 工具新生成，没有使用 CLI / API 回退；未使用外部图片作为输入。
- 视觉：纸张质感、深绿色墨色与少量朱红色；封面不是应用截图，也不是课程知识图解。
- 生成后直接复制到仓库，保留原图。没有将第三方项目的插图或 Logo 搬入本项目。

最终生成提示词：

```text
Use case: stylized-concept. Asset type: original wide GitHub repository cover illustration for an open-source university exam preparation Agent Skill named EXAM PREP. Primary request: a sophisticated editorial illustration of a semester of scattered study material becoming three carefully organized study booklets. Create a finished horizontal banner, approximately 2.4:1 aspect ratio, ideally 2400 by 1000 pixels. Scene: a warm ivory paper background, subtle fine paper grain, refined dark evergreen ink and very restrained vermilion red accents. Composition: on the left third, generous negative space with the exact large headline 'EXAM PREP' in a beautiful high-contrast editorial serif typeface, split over two lines if needed, and a tiny neatly letterspaced 'FROM NOTES TO KNOWLEDGE' below. On the right two thirds, an elegant tangible paper sculpture: a few loosely layered lecture pages, a notebook with restrained hand-drawn geometric sketches, a small annotated exam sheet, curving paper ribbons organizing into exactly three upright slim ivory booklets. One booklet has an abstract branch diagram, one has orderly question-number dots and blank answer lines, one has small restrained correction marks. Use dark evergreen book spines and thin red page markers. No readable microtext on pages, no pseudo-Chinese writing. Style: premium educational publishing art direction, meticulous cut-paper mixed with subtle 3D depth and tactile uncoated stock, realistic soft shadows, asymmetrical but balanced, calm and intelligent, ample breathing room, crisp edges. Objects feel like real paper. Constraints: all objects fully inside frame, no watermark, no third-party logos, no people, no robots, no graduation cap, no neon, no purple gradient, no dashboard or fake software screenshot. This is conceptual cover art, not a technical workflow diagram. Only readable text allowed is 'EXAM PREP' and 'FROM NOTES TO KNOWLEDGE'.
```

## 实际成果预览

以下图片由仓库中已有 PDF 的第一页直接渲染，使用 PyMuPDF，未以图像模型改写内容。

| 图片 | 对应 PDF |
| --- | --- |
| `assets/readme/summary-preview.png` | `examples/mini-course/preview/knowledge-summary.pdf` |
| `assets/readme/exam-preview.png` | `examples/mini-course/preview/mock-exam-01.pdf` |
| `assets/readme/answers-preview.png` | `examples/mini-course/preview/mock-exam-01-answers.pdf` |

模拟卷共有两页，首页预览点击后可以查看完整 PDF。样例为原创微型课程的格式演示，不代表所有课程或模型的产出质量。

## 参考与范围

文档呈现与可调参数组织方式参考 [Taste Skill](https://github.com/Leonxlnx/taste-skill)。本项目独立编写课程复习规则和说明，未复制其前端工程指令，也未声称获得其作者背书。
