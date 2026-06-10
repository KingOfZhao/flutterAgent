# 评测门禁操作手册:飞轮四步的工具链落地

> 把 `capability-fixation.md` §8 的强化飞轮(筛/判/修/门)映射到本仓库可执行的脚本与文件。
> 时点:2026-06-10。理论见 `capability-fixation.md`,方法论见 `claude-eval-methodology.md`。

## 0. 文件布局(eval/ 目录,运行期生成)

| 文件 | 由谁产生 | 作用 |
|---|---|---|
| `eval/candidates.jsonl` | `scripts/harvest_failures.py`(①筛,全自动) | 从 runs.jsonl 收割的失败候选 |
| `eval/drafts.jsonl` | `scripts/triage_candidates.py`(②判,半自动) | 带 `TODO(判)` rubric 模板的草稿样本 |
| `eval/samples.jsonl` | 人工把写完 rubric 的草稿移入(②判,人工收尾) | 正式评测集(含 working + sealed) |
| `eval/results_*.jsonl` | judge 跑分(执行可外包给模型) | 每样本 `{sample_id, hard_pass, quality}` |

## 1. 四步流水线

```
runs.jsonl ──①筛──> candidates.jsonl ──②判──> drafts.jsonl ──人工写 rubric──> samples.jsonl
                                                                      │
变更(skill/prompt/模型) ──③修──> 候选版本跑 judge ──④门──> eval_gate.py(exit 0/1)
```

- **①筛(全自动)**:`python scripts/harvest_failures.py`。候选条件即 `_failure_reasons`:
  final_review_blocking / acceptance_gaps / bad_package / invalid_stage。
- **②判(人不可缺位)**:`python scripts/triage_candidates.py` 只生成模板;
  每条 `TODO(判)` 必须被替换为**可判定**的否决项/打分维度,否则 `is_draft()` 为真,
  门禁自动排除该样本。这是防 judge 偏差进入门禁的设计,不是偷懒的占位。
- **③修**:对失败机制做修复(skill/prompt/代码),修复说明必须声明"针对哪条失败机制"。
- **④门(全自动,可进 CI)**:
  ```
  python scripts/eval_gate.py --baseline eval/results_baseline.jsonl \
      --candidate eval/results_candidate.jsonl
  ```
  exit 0 = 通过(tie/improved),exit 1 = 阻断。

## 2. 门禁判定规则(与理论一一对应)

| 规则 | 理论出处 |
|---|---|
| 任一样本 hard_pass 由真变假 → 阻断 | 棘轮"否决项一票否决"(eval-methodology §1.3) |
| baseline 有结果、candidate 缺结果 → 阻断 | 覆盖率静默下降本身就是回归 |
| 平均 quality 跌幅 > 噪声带(默认 0.05)→ 阻断 | "不劣于+噪声判平"(capability-fixation §2) |
| 噪声带内 → tie(通过但不许宣称提升) | 防 Goodhart:平局不许当成进步 |
| 涨幅 > 噪声带 → improved | 只有越过噪声带才允许宣称改进 |

## 3. 封存集纪律

- `eval_store.is_sealed(id)` 按 id 的 sha256 确定性分桶(默认 20%),样本永不在
  working/sealed 之间迁移。
- 日常迭代只对 working 集跑门禁;封存集**只在发版/大变更前**解封跑一次,
  跑完立即把这次解封记录在案(日期+原因)。频繁解封 = 封存集失效 = D6(评测过拟合)。

## 4. 反模式

- 在 rubric 里写不可判定的形容词("更优雅")——judge 偏差直通门禁。
- 用同一个模型既生成产出又当 judge 还写 rubric——验证定义权外包,见 capability-fixation §7。
- 草稿没写完就改 `TODO(判)` 文案绕过 `is_draft`——绕过的不是检查,是自己的棘爪。
- 把 smoke 样本(kind=smoke)当回归证据——smoke 只证明链路通,不证明质量。

## 诚实边界

- judge 跑分环节(③→④之间)本仓库尚未提供脚本:judge 的选择与校准依
  `claude-eval-methodology.md` §1.4,需接真实模型后落地。
- 噪声带 0.05 是先验默认值,应在积累 ≥3 次重复跑分后用实测方差校准。
