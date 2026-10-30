# Training: not applicable

I didn't fine-tune or train anything. The model was a third-party derivative used as published.

That's deliberate. The useful question for this bench isn't how to change a model; it's what the host and harness let a model I didn't build *do*. The research that reframed this work showed how little a poisoned fine-tune costs, which is a reason to vet and contain weights, not to make more of them.

If that changes, training would need its own threat model: data provenance, where training runs, what the resulting weights can reach, and how they're verified before use.
