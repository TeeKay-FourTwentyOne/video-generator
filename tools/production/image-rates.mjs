/** Google image usage record → list-price estimate for ledger reconciliation.
 * Rates checked 2026-10-03 against https://cloud.google.com/vertex-ai/generative-ai/pricing
 * (Gemini 3 Pro Image): input text/image $2 per million tokens; output image $120 per
 * million tokens (a 1K/2K image is 1120 tokens, 4K is 2000); output text and thinking
 * $12 per million. These are estimates from saved usage, not invoice-confirmed charges.
 */
export const GOOGLE_IMAGE_RATES = Object.freeze({ checked: '2026-10-03', model: 'gemini-3-pro-image',
  inputPerMillion: 2, outputImagePerMillion: 120, outputTextPerMillion: 12 });

export function imageUsageCost(record, rates = GOOGLE_IMAGE_RATES) {
  const u = record?.usage;
  if (!u || !Number.isFinite(u.promptTokenCount) || !Number.isFinite(u.candidatesTokenCount))
    throw new Error('Usage record lacks token counts; reconcile manually from billing evidence');
  const imageOut = (u.candidatesTokensDetails ?? []).filter(d => d.modality === 'IMAGE').reduce((n, d) => n + d.tokenCount, 0);
  const textOut = u.candidatesTokenCount - imageOut + (u.thoughtsTokenCount ?? 0);
  const usd = (u.promptTokenCount * rates.inputPerMillion + imageOut * rates.outputImagePerMillion + textOut * rates.outputTextPerMillion) / 1e6;
  return { usd: Math.round(usd * 1e6) / 1e6, inputTokens: u.promptTokenCount, imageOutputTokens: imageOut, textOutputTokens: textOut,
    evidence: `Saved usage: ${u.promptTokenCount} input, ${imageOut} image-output, ${textOut} text/thinking tokens at ${rates.model} list rates checked ${rates.checked}` };
}
