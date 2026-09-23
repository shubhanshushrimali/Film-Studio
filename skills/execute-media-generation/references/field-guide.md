# Field Guide

## Job states

Allow only these transitions:

- `queued` to `running`, `canceled`, `failed`, or `blocked`
- `running` to `succeeded`, `failed`, or `canceled`
- terminal states remain terminal; a retry creates a new attempt under the same request ID

## Retry classes

- Retry transport timeouts, provider overload, and explicitly retryable server errors.
- Do not automatically retry invalid parameters, unsupported modes, authentication failures, spend-limit failures, or content-policy rejection.
- Reuse the idempotency key when reconciling the same provider submission.
- Derive a new attempt ID, but preserve the stable compiled request ID, when a real retry is authorized.

## Media persistence

Treat a provider result as successful only after:

1. the provider reports completion;
2. the output can be read;
3. the output is copied into durable project storage;
4. media type and basic metadata are verified;
5. a checksum and producing job ID are recorded.

## Cost

Record provider, model, price basis, estimated amount, actual amount, currency, and billable units. Block before submission when the declared hard limit would be exceeded.
