# Qualified generation rates

Checked 2026-10-03 against [Google's official pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing#veo).
Reverify for each new production; a stored estimate is not a billing invoice.

| Veo 3.1 GA | Resolution | Audio | USD/second | Eight-second attempt |
| --- | --- | --- | ---: | ---: |
| Quality | 720p / 1080p | No | 0.20 | 1.60 |
| Quality | 720p / 1080p | Yes | 0.40 | 3.20 |
| Fast | 720p | No | 0.08 | 0.64 |
| Fast | 1080p | No | 0.10 | 0.80 |
| Fast | 720p | Yes | 0.10 | 0.80 |
| Fast | 1080p | Yes | 0.12 | 0.96 |

The executable quote is `src/production/veo-spec.ts` inside the MCP package.
Qualified requests use exact 4, 6 or 8 seconds; there is no silent duration snapping.
The default is Quality, 1080p, eight seconds, audio on. Set every parameter explicitly
in production plans. Both short and `-prod` aliases now resolve to the GA models.
The [GA model card](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
is the capability boundary; this adapter does not expose unqualified 4K, reference
asset arrays, video extension or newer Lite variants just because pricing lists them.

One authorized pot covers **all** paid services, not just Veo. Every attempt is
reserved before submission. Failures and uncertain outcomes retain their reserve
until evidence supports reconciliation; this conservative policy is not a claim
that every failed request is billed. Do not automatically retry paid requests.

The bounded Google image route uses Gemini 3 Pro Image at 2K, at most three
references and 6,144 maximum output tokens. It reserves $0.80 per request and saves
usage metadata. Current listed prices: $2/M input tokens, $12/M text/reasoning
output tokens, $120/M image output tokens. Use the actual modality counts for an
estimate; retain a separate infrastructure allowance. [Google image pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

Legacy QA, transcription, ElevenLabs and image helpers have provider- and
account-specific charges. Reserve an explicit allowance in the film ledger before
using them; do not copy old flat per-call guesses into a new authorization.
The qualified QA default, [Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview),
lists $2/M input and $10/M output tokens. Its exact-model cost entry precedes old
family fallbacks. Existing historical ledger lines are retained, not rewritten.
Built-in subscription tools with unreported usage should not be described as
metered $0 API generation.

There is no mandatory Fast-then-Quality pass. Choose a model for the shot and
compare the cost of **accepted edited seconds**, including references, retries,
review and sound. A seed is provenance, not a guarantee of matching pixels or
cross-model continuity. See [the provider comparison](docs/video-model-options-2026-10.md).
