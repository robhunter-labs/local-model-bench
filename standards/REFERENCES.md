# Standards and references (stubs)

Links and short pointers only. Nothing here reproduces a standard's text. The mapping columns are deliberately thin; filling them in properly is part of the remaining work.

| Reference | Why it's here | Maps to (draft) | Status |
| --- | --- | --- | --- |
| [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) | Shared vocabulary for LLM risks: prompt injection, sensitive information disclosure, supply chain, excessive agency, misinformation, unbounded consumption and others | T03, T04, T08, T09, T10, T14 | stub |
| [OWASP GenAI Security Project](https://genai.owasp.org/) | Agentic-AI threat and mitigation guidance alongside the Top 10 | T04, T10 | stub |
| [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework) | Govern, map, measure, manage: a frame for writing down why each control exists | whole repo | stub |
| [NIST AI 600-1, Generative AI Profile](https://doi.org/10.6028/NIST.AI.600-1) | The RMF applied to generative AI | whole repo | stub |
| [MITRE ATLAS](https://atlas.mitre.org/) | Adversary techniques against AI systems; useful for naming pen-test methods | P07, P09, P10 | stub |
| [NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final) | Technical guide to security testing; structure for the pen-test plan | pentest/ | stub |
| [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) | Host hardening baseline for the inference machine's operating system | C02, C04 | stub |
| [Ollama documentation](https://docs.ollama.com/) | Runtime settings: binding, cloud, context, parallelism | C01, C05, C09 | referenced |
| [ProjectDiscovery: "How abliterated models can get you pwned"](https://projectdiscovery.io/research/how-abliterated-models-can-get-you-pwned) | The research that reframed the model as an unreviewed pull request with a shell | T03, T08 | referenced |
| [Pi](https://pi.dev) | Minimal agent harness used as the target harness | setup/HARNESS_PI.md | referenced |

Mapping to a standard is a claim about coverage, so each row stays a stub until someone does the mapping and writes down what was left out.
