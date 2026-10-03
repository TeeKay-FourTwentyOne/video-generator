# Video models worth testing next

Research checked 2026-10-03. No new-provider account, SDK, upload or generation API
was used. Prices below are advertised API prices, before applicable tax; account
access and actual output quality were not tested. Scenario fit is our inference
from documented controls and the Borrowed Light production, not a benchmark result.

## Shortlist by production need

| Option | Documented cost example | Best next test here | Important limit |
| --- | --- | --- | --- |
| **Runway Gen-4 Turbo / Gen-4.5** | Turbo $0.05/s; Gen-4.5 $0.12/s, using $0.01 credits | Cheap anchored motion, then a harder lamp-transfer shot; test Aleph separately for repairing existing footage | Formats and advanced edits have separate charges; generated silence still needs a soundtrack |
| **MiniMax Hailuo 2.3 Fast / H3** | Hailuo Fast: $0.19 for 6s at 768P, $0.33 for 6s at 1080P. H3: $0.08/s at 768P, $0.13/s at 2K | Low-cost atmospheric inserts; H3 for shots with multiple references or source motion | Video reference seconds are additionally billed; Hailuo 2.3 is now in the legacy pricing section |
| **Luma Ray 3.2** | SDR 5s: $0.30 at 720p, $1.20 at 1080p; 10s: $0.90 / $3.60 | Book-ended transitions and targeted video repair; preserve source motion while changing appearance | The new Agents API differs from the older Ray 2 Dream Machine API; editing, extension, reframing and HDR have different rates |
| **Kling 3.x / Omni** | Direct current price not independently recoverable from the script-rendered pricing page in this review | Character references, sustained action and multiple-keyframe control | Qualify exact model, endpoint, duration, reference and audio limits before estimating or integrating |
| **LTX-2.5 local / LTX Desktop** | No per-generation provider fee for local execution; hardware, power and storage are real costs | Persistent control, repeatable experiments, local motion/reference workflows | Current Python reference requirements exceed this checkout's available disk; Desktop has a separate hardware path |

Runway's [official model catalog](https://docs.dev.runwayml.com/guides/models/) lists
Gen-4.5 text/image-to-video and Aleph editing. Its [pricing](https://docs.dev.runwayml.com/guides/pricing/)
also exposes other companies' models, but that is still a new Runway provider
relationship for this repository. Do not silently route existing Google requests
through an aggregator. A narrow direct Runway trial is the strongest first API
candidate because it tests both cheap motion and a distinct repair workflow.

MiniMax's current [pay-as-you-go table](https://platform.minimax.io/docs/guides/pricing-paygo)
separates output and reference-material billing. H3 includes the first five image
references, then charges for additional images; reference video is priced by its
duration and output resolution. Hailuo's short low-cost clips are useful candidates
for rain, fog, fabric and secondary motion where continuity failures can be cut
around. Availability of a listed legacy model still needs account-level checking.

Luma's current [quickstart](https://docs.agents.lumalabs.ai/) names `ray-3.2` and
supports start/end images. [Video editing](https://docs.agents.lumalabs.ai/guides/videos/editing/)
is a distinct operation, potentially useful for preserving a successful performance
while correcting look or setting. The [pricing table](https://docs.agents.lumalabs.ai/guides/pricing/)
lists 720p SDR editing at $1.08/5s and $2.16/10s. Do not extrapolate the generation
rate to edits or assume 10 seconds costs twice a five-second generation. Its
pay-as-you-go offering does not carry the provisioned tier's no-training guarantee;
review terms before uploading private character references.

Kling's [developer landing page](https://kling.ai/dev/api) and
[quickstart](https://kling.ai/document-api/guides/get-started/quick-start) are the
appropriate starting points. Search-indexed feature descriptions indicate Omni
references and keyframe controls, but the fetched pricing page was empty. No price
or superiority claim is warranted from reseller tables. Treat Kling as a research
candidate until its direct API contract is verified.

LTX's [reference requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements)
currently specify a 32 GB+ NVIDIA GPU and 100 GB free storage. The separate
[official Desktop repository](https://github.com/Lightricks/LTX-Desktop) supports
Apple Silicon as well as selected NVIDIA systems, with model/license requirements
that must be checked for the chosen path. About 18 GiB was free at review start.
No models or libraries were downloaded, and no existing assets were deleted.

## The Google path still has room to improve

The qualified client remains on the existing official Vertex endpoint and GA
Veo 3.1 models; this baseline did not need a provider migration. Google lists
[Veo 3.1 Lite](https://cloud.google.com/blog/products/ai-machine-learning/veo-3-1-lite-and-a-new-veo-upscaling-capability-on-vertex-ai)
as a cheaper tier. Its [pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing#veo)
lists silent Lite at $0.03/s (720p) or $0.05/s (1080p). That is worth a later
qualification for background motion. It is not yet advertised by this adapter:
pricing alone does not establish account access or parameter compatibility.

## A concrete audition using this film

Reuse the preserved starting anchors and intent from Borrowed Light for three
tests: the machine approaches a fixed planter; its gripper removes one lamp;
light grows through an unchanged tree silhouette. Add a fourth **edit** test using
the rejected bulb-transfer coverage. These expose distinct failure mechanisms.

Keep aspect, source anchors and evaluation criteria fixed, but use each provider's
supported native duration. Record latency, full quote, actual charge, source hashes,
identity/prop changes, clean editable range and audio requirements. Inspect both
whole clips and dense transfer windows. Evaluate **cost per accepted edited second**,
including references, failures and sound, rather than advertised generation price.
Permit one initial attempt per case and only a specifically justified retake.

Do not implement five speculative adapters now. The next adapter should earn its
place by producing a shot or repair the current toolkit cannot do reliably. It
must satisfy the same budget, idempotency, terminal-state, local-download and
provenance contracts before it becomes part of production.
