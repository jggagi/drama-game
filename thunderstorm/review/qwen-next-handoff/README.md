# 《雷雨：门外》Qwen Next 试听交接

接手任务：先完成一条中年男声旁白试听，再生成所选 20 句人物对白与旁白，验证后更新并发布现有私有 Sites 站点。用户已明确授权生成、修改和发布，无需再次确认配音要求。

## 当前事实（2026-10-04，北京时间）

- [现有站点](https://menwai-two-packings.jggagi.chatgpt.site/) · [现有试听页](https://menwai-two-packings.jggagi.chatgpt.site/?mode=qwen)。
- Sites 项目 ID：`appgprj_6ac10b6aef288191b1166c8b35161c79`。最近确认版本为 **15**；接手时查当前版本。
- 站点为用户私有，保留当前访问设置。GitHub 仓库公开，仓库可见性不代表站点访问权限。
- 原站 20 句试听使用 `qwen3-tts-instruct-flash-2026-01-26`，侍萍、鲁贵使用 `qwen3-tts-vd-2026-01-26`，尚未发布 Next 版。
- 已实际调用 **`qwen-audio-3.1-tts-next`** 一次，返回 **HTTP 200、`output.finish_reason=stop`**。请求 ID：`403d043e-34e9-9e57-b034-ffeec76d99a1`，API 报告音频时长 8 秒。该次模型调用及鉴权已成功，不能再把旧阻塞归因于密钥错误或模型不可用。
- 音频下载请求收到 403；对下载域名的无鉴权检查确认代理 **CONNECT 403**。尚未下载任何 Next WAV，也未核验其台词、人物年龄感或声线一致性。
- 20 句请求已准备并检查原文、逐句要求、字段与角色描述；此批次准备工作未调用 API。
- Sites 源码曾恢复至 `/workspace/menwai-site`，提交 `a2f9a71af9819226633eb95135ad067c64c19176`；原版类型检查与生产构建通过。本站源码未修改，未发布新版本。

可机器读取的状态见 [state.json](state.json)。

## 首先检查环境

先阅读 **cloud-environment-runtime、sites-building、sites-hosting** 技能。使用当前聊天的环境状态工具与 `/etc/codex/network-policy.json` 检查实际配置；交接时最新观察为 `observations_current=true`、网络 `enforced`、密钥 `ready`，但网络允许域名仍只有前两项，缺少音频下载域名。不要把旧环境观察当作新环境就绪证据。

drama-game cloud 的网络允许域名应分别包含三项：

```text
dashscope.aliyuncs.com
ws-zf7l1ljexja2bd6z.cn-beijing.maas.aliyuncs.com
dashscope-result-bj.oss-cn-beijing.aliyuncs.com
```

`DASHSCOPE_API_KEY` 的允许域名需要前两项。下载音频不携带 API 密钥，第三项只需在网络允许域名中。保留继承的系统代理、CA 信任与 TLS 校验，不绕过网络策略，不打印密钥，不要求用户粘贴密钥。保存 cloud 配置后，从更新后的配置创建新聊天环境。

原缓存响应位于旧环境 `/workspace/scratch/qwen-next-audition/narrator-probe-response.json`，含临时签名下载 URL，**不入库、不发布到站点源码**。原 URL 标示到期为北京时间 **2026-10-05 19:43:34**。

若缓存仍可访问，先下载这条已付费合成的旁白。GitHub 不包含该响应，单靠仓库不能恢复其 URL；新环境缺失缓存时，确认下载域名已可访问后再显式生成一次新的首句。不要为了检查下载权限连续合成。

## 恢复现有 Sites 源码

若 `/workspace/menwai-site` 不存在，调用 Sites 工具，按技能的“Open a Site”流程恢复同一项目最新源码。不要新建项目、重新搭站，也不要用这个 GitHub 交接目录替换完整站点源码。

优先读取 Sites 项目内：

- `review/qwen-audition/selection.json`：20 句原文、角色、场景、逐句表演要求。
- `review/qwen-audition/cast-v2.json`：原角色设定。
- `src/qwen-audition/manifest.json`：现有音频映射。
- `src/qwen-audition/app.ts`：试听页面。
- `docs/qwen-audition-notes.md`：既有记录。

本目录的 [selection.json](selection.json) 与 [manifest-v2.json](manifest-v2.json) 是第 15 版交接快照，用于核对。当前 Sites 内容有变化时先比对，不盲目覆盖。

## 模型与表演

```text
POST https://ws-zf7l1ljexja2bd6z.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer
Authorization: Bearer 环境变量 DASHSCOPE_API_KEY
model: qwen-audio-3.1-tts-next
```

用 `input.text_prompt` 描述角色与逐句表演，区隔准确原文；不使用旧 Flash 的 `voice/instructions` 字段，也不复用旧音色 ID。参数为 `format=wav`、`sample_rate=24000`、`channels=1`、`volume=50`、`rate=1.0`。同角色固定描述与 seed，旁白 seed=42；seed 不能保证音色一致，仍须试听。

所有录音使用清晰普通话干声，无音乐、音效或额外旁述，保留原台词。

| 声部 | 年龄与表演要求 |
| --- | --- |
| 旁白 | 约50岁男性，低中音厚实、略微沙哑、有沧桑感，沉静克制、语速略慢 |
| 四凤 | 18岁，清澈朴素、谨慎而有主见 |
| 侍萍 | 47岁，成熟中低音、经历磨砺、护女坚定 |
| 繁漪 | 35岁，体面、压抑、带锋芒 |
| 周萍 | 28岁，温和、不安、负罪与逃避 |
| 周冲 | 17岁，清朗少年、真诚、有理想 |
| 周朴园 | 55岁，结实低音、端持、惯于掌控 |
| 鲁大海 | 27岁，粗粝有力、直接、愤怒而有条理 |
| 鲁贵 | 48岁，略哑、世故、市侩、善于算计 |

角色描述见 [cast-next.json](cast-next.json)，20 个完整请求位于 [prepared/](prepared/)。[narrator-probe-request.json](narrator-probe-request.json) 保留实际已调用的旧探针提示；它与 prepared 第一句提示有差别，复用时应记录实际来源。

## 续跑方式

生成脚本需要 Python、`ffmpeg` 与 `ffprobe`；分析脚本另需 NumPy。先只检查本地请求，不产生 API 费用：

```sh
python thunderstorm/review/qwen-next-handoff/generate-next.py --validate-only
```

`generate-next.py` 支持 `--project-dir`、`--work-dir`、`--requests-dir`，默认源码目录 `/workspace/menwai-site`，输出与缓存目录 `/workspace/scratch/qwen-next-audition`。缓存与临时 URL 保持在仓库外。默认遇到缺失、失败或过期缓存会停机，不自动重复付费合成。

缓存可用时，先取回并技术检查首句：

```sh
python thunderstorm/review/qwen-next-handoff/generate-next.py --probe-only
```

确实缺失缓存或链接已过期时，显式生成新旁白。脚本先检查下载域名能到达，遭 CONNECT 403 时不合成：

```sh
python thunderstorm/review/qwen-next-handoff/generate-next.py --probe-only --new-probe
```

旁白通过技术检查和实际试听后，继续其余句子：

```sh
python thunderstorm/review/qwen-next-handoff/generate-next.py
python thunderstorm/review/qwen-next-handoff/analyze-wav.py /workspace/scratch/qwen-next-audition/wavs --output /workspace/scratch/qwen-next-audition/audio-report.json
```

每次必须确认 `output.finish_reason=stop` 后下载 `output.audio.url`，保存成功响应以供续跑。若下载域名仍被拦截，报告实际域名并停止后续合成；不要把下载阻塞当作模型失败。失败缓存不会自动重试，应先排查具体错误。生成脚本不修改站点。

## 验证与发布

1. 对 20 段全量解码，检查格式、时长、空音、削波与明显截断风险。分析脚本只做技术检查，不执行 ASR，也不验证人物身份。
2. 实际试听并逐字核对原文；同角色连续试听，检查年龄、性格、音色及情绪的一致性。不能把声学指标当作台词或演出核验。无法实听时如实报告未验证项。
3. 更新现有 `?mode=qwen` 试听页，明确标示实际 Next 模型。保留旧 Qwen 试听对照、原剧情录音与进度功能，不将试听写入剧情存档。
4. 音频采用站点内可稳定播放的本地资源和内容哈希文件名，临时下载 URL 不进入源码。保留原 manifest 作为对照，合辑保留逐句定位、暂停、续播与下载。
5. 更新生成证据及 `docs/qwen-audition-notes.md`，执行生产构建与适当的实际播放验证；已有浏览器专项 `tests/qwen-audition-browser.mjs` 的旧模型断言需随新清单调整。
6. 由接手主代理按 Sites 工作流推送准确源码、打包、保存并发布到同一私有项目，确认部署成功。未经用户要求不改变访问范围。
7. 最后交付实际模型、可播放试听结果、更新后的站点链接和真实验证限制。配置或权限阻塞应给出实际检测结果及具体修改项，不重复询问已明确的配音要求。

新聊天可直接发送：**“读取 drama-game 仓库 thunderstorm/review/qwen-next-handoff/README.md，继续 Qwen Next 20 句试听并更新现有私有站点。”**
