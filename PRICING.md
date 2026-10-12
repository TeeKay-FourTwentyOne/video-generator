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

## MiniMax direct V2 API

Checked 2026-10-11 against [MiniMax pay-as-you-go pricing](https://platform.minimax.io/docs/guides/pricing-paygo).
The implementation is `mcp/video-generator/src/production/minimax-spec.ts`.
Live generation and invoice reconciliation are pending; these are list-price reservations.

| Model | Resolution | Output USD/second | Reference video USD/second | Image inputs |
| --- | --- | ---: | ---: | --- |
| H3 Max | 480P | 0.05 | 0.0553 | First 2 free, then $0.074 each |
| H3 Max | 768P | 0.08 | 0.143 | First 2 free, then $0.074 each |
| H3 | 768P | 0.08 | 0.08 | First 5 free, then $0.04 each |
| H3 | 2K | 0.13 | 0.13 | First 5 free, then $0.04 each |

Input audio is free. Quotes include the output plus image/video inputs. The adapter
measures local reference durations and conservatively rounds each video up to a
whole second for reservations because fractional billing is not specified.
At 768P, six output seconds on H3 Max reserve $0.48 with one starting image;
adding a two-second reference video in reference mode adds $0.286. Frame mode and
reference mode cannot be mixed. Taxes and other production work require their own
allowance in the same ledger. No failed reservation is automatically refunded.
See [MiniMax setup](docs/minimax.md) for supported controls and recovery.

## Runway direct API

Checked 2026-10-11 against [Runway API pricing](https://docs.dev.runwayml.com/guides/pricing/).
One API credit costs USD 0.01. The adapter supports native silent MP4 only:

| Model | Credits/second | USD/second | Eight-second attempt |
| --- | ---: | ---: | ---: |
| Gen-4.5 | 12 | 0.12 | 0.96 |
| Gen-4 Turbo (starting image required) | 5 | 0.05 | 0.40 |

Runway's web subscription and API balances are separate. Tax, anchor generation,
audio and optional post-processing are outside these video quotes. The executable
quote is `mcp/video-generator/src/production/runway-spec.ts`. Terminal task
`cost.credits` supports explicit `reconcile-runway`; missing or ambiguous evidence
does not release a reservation. [Setup and API limits](docs/runway.md).

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
