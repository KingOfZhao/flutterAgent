# eval/ — 产出质量评测集工作目录

用法与纪律见 `knowledge/eval-gate-operations.md`。

- `smoke_samples.jsonl`(入库):3 条 kind=smoke 冒烟样本,只证明评测链路可跑通,
  **不作为回归质量证据**;regression 样本必须来自真实失败的收割与人工判读。
- `candidates.jsonl` / `drafts.jsonl` / `samples.jsonl` / `results_*.jsonl`:运行期生成,不入库。
