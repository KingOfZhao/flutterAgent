# eval/ — 产出质量评测集工作目录

用法与纪律见 `knowledge/eval-gate-operations.md`。

- `smoke_samples.jsonl`(入库):3 条 kind=smoke 冒烟样本,只证明评测链路可跑通,
  **不作为回归质量证据**;regression 样本必须来自真实失败的收割与人工判读。
- `candidates.jsonl` / `drafts.jsonl` / `samples.jsonl` / `results_*.jsonl`:运行期生成,不入库。
- `degradation_thresholds.json`(入库):退化检测阈值与标定元数据(`calibrated_at`/`basis`),
  改阈值必须走 git 提交——见 `capability-fixation.md` §10 的可审计纪律。
- `corpus_baseline.json`:`scripts/corpus_drift.py snapshot` 生成的 D3 基线,运行期生成,不入库。
