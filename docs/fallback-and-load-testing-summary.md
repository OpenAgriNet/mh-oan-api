# Executive Summary — MH Vistaar: Fallback Models & Load Testing

## Overview

The MH Vistaar AI platform uses a **dual-provider inference architecture** to ensure reliability at scale. Primary inference runs on **self-hosted vLLM** (a fine-tuned Vistaar model for conversational flows and GPT-OSS Safeguard 20B for moderation), with **Azure OpenAI** configured as an automatic fallback. This design provides cost efficiency and data locality during normal operations, while guaranteeing service continuity when primary infrastructure is unavailable.

## Fallback Design

Failover from vLLM to Azure is **automatic and transparent** to the application. It triggers only on genuine infrastructure failures — connection timeouts, server errors (5xx), malformed responses, or concurrency overflow. It does **not** trigger on low-quality answers, moderation rejections, or client-side (4xx) errors, as these do not indicate a provider failure.

Agrinet and moderation traffic use **independent vLLM endpoints**, so a failure on one flow does not impact the other. Azure serves as a single shared fallback for both.

## Design Priority: Latency Over Queue Depth

The platform is currently tuned to **prioritize fast response times over maximum resource utilization**. When concurrent calls to the MahaVistaar LLM approach the configured cap, the system does **not** queue incoming requests and let them wait — instead, it **immediately and seamlessly routes overflow to Azure OpenAI**. This is a deliberate trade-off: users never experience elevated latency or timeouts due to queuing, even at peak load.

**How it works in practice:**

- Once 100 concurrent calls are active on the main MahaVistaar LLM, the 101st request is instantly served by Azure OpenAI.
- The transition is completely transparent to the end user — same API, same response format, no retries or delays.
- vLLM continues serving its in-flight requests at full speed, and new capacity reopens as requests complete.

**Tunable for future efficiency:**

This 100-concurrent-call threshold is a configurable value (via environment variables), not a hard architectural limit. As we gather more production data on request latency distribution, GPU utilization, and fallback cost, we can raise the cap to drive more traffic to the cheaper self-hosted inference — improving cost-efficiency while maintaining the same latency guarantees. Similarly, we can introduce a small queue buffer if we observe that short bursts would benefit from brief waiting rather than immediate fallback.

**Current posture: reliability and speed first; efficiency optimization second.** This ensures a consistent user experience during launch and stabilization, with clear levers to optimize as the platform matures.

## Load Testing & Capacity

Empirical testing and mathematical modeling (Little's Law) were used to determine the platform's concurrency ceiling:

- **Moderation flow** — Lightweight (1–2 s per call) and not the bottleneck. Effectively supports ~1,000 concurrent users before saturation.
- **Mahavistaar flow** — The constraining path. Each user question generates roughly 3 vLLM calls (tool selection, response generation, suggestions), each holding a slot for ~5 seconds on average.

**Derived capacity:**

- **~80 concurrent active users** under ideal conditions
- **~60–70 concurrent users** as the safe operational range, accounting for bursty traffic patterns

Load tests at 10, 25, and 60 users/minute did **not** trigger fallback, because user think-time and the sequential nature of multi-turn calls naturally smoothed demand below the concurrency cap.

## Observability — Langfuse Integration (In Progress)

The **Langfuse server has been provisioned**, and integration with the MH Vistaar platform is planned for deployment in the next couple of days. Once live, Langfuse will provide detailed operational visibility, including:

- **Provider split metrics** — exactly how many requests are served by the self-hosted MahaVistaar model vs. Azure OpenAI, over any time window
- **Fallback frequency and triggers** — when and why fallback events occurred
- **Per-request latency, token usage, and cost** — broken down by provider, model, and flow (agrinet, moderation, suggestions)
- **Trace-level debugging** — full visibility into multi-turn conversations and tool calls

This observability layer is essential for making informed decisions about when to raise the concurrency cap, how to size infrastructure, and where to optimize cost. It will replace indirect inference with direct measurement of production behavior.

## Key Insights

1. **Fallback is working as designed** — triggered deterministically by concurrency or infrastructure failures, not quality issues.
2. **Mahavistaar is the capacity bottleneck**, not moderation — multi-turn tool orchestration amplifies load per user.
3. **User think-time materially extends capacity** — real-world traffic rarely achieves peak concurrency even at high request counts per minute.
4. **The system handles burst traffic gracefully** — overflow spills to Azure without user-visible errors.

## Operational Recommendations

- Monitor concurrent in-flight requests on vLLM; set alerting at 70% of capacity.
- Plan infrastructure scaling (additional GPU capacity or workers) when sustained concurrent users exceed ~50.
- Keep Azure fallback provisioned with headroom for full traffic absorption during any vLLM outage.
- Once Langfuse is integrated, use provider-split metrics to inform concurrency-cap tuning and cost optimization.
- Treat the 60–70 user safe range as the current SLA boundary; scale before this threshold is reached.
