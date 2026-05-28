# LLM-Local Context

LLM-Local is a local workstation control surface for model serving, training,
evaluation, and observation across multiple local LLM runtimes.

## Language

**Serving Runtime**:
A concrete backend that loads or hosts models and answers inference requests.
_Avoid_: backend when the runtime boundary matters.

**Model Registry**:
The inventory of downloaded local model artifacts and the runtimes they can serve.
_Avoid_: model database.

**Serving Target**:
A runtime that a registry entry is compatible with.
_Avoid_: active runtime.

**Serving Preset**:
A user-facing workflow binding that selects a model, serving runtime, and LiteLLM alias together.
_Avoid_: profile, model profile, environment profile.

**Active Serving State**:
Generated local state recording which serving preset is currently selected.
_Avoid_: source preset, registry entry.

**Gateway Alias**:
A stable LiteLLM model name that clients use instead of direct runtime model names.
_Avoid_: model id when referring to the client-facing alias.

**Client Service**:
A local API or UI surface that consumes the LiteLLM gateway rather than loading
models itself.
_Avoid_: serving runtime when the component does not host model weights.

**Compose Profile**:
A Docker Compose opt-in service group such as `gpu`, `batch`, or `quality`.
_Avoid_: profile when discussing model selection workflows.

## Relationships

- A **Model Registry** entry has one or more **Serving Targets**.
- A **Serving Preset** chooses one **Serving Runtime** and one **Gateway Alias**.
- **Active Serving State** is generated from exactly one **Serving Preset**.
- A **Gateway Alias** points to the model currently configured behind a **Serving Runtime**.
- A **Client Service** calls the LiteLLM gateway through a **Gateway Alias**.
- A **Compose Profile** is infrastructure lifecycle configuration, not model selection state.

## Example Dialogue

> **Dev:** "Should `chat-small` be a profile?"
> **Domain expert:** "No. `profile` already means Docker Compose profile here. `chat-small` is a Serving Preset because it binds model, runtime, and gateway alias."

## Flagged Ambiguities

- "profile" was considered for model workflow switching, but this conflicts with
  existing Docker Compose profile terminology. Resolved: use **Serving Preset**
  for model/runtime workflow bindings.
