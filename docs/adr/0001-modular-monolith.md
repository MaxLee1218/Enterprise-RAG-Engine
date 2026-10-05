# ADR-0001: Keep a modular monolith

- Status: Accepted
- Context: The project needs explicit ingestion, retrieval, generation,
  orchestration, and transport boundaries, but has no measured requirement for
  independent scaling or deployment.
- Decision: Compose focused modules in one process through narrow interfaces
  and dependency injection.
- Consequences: Local operation and testing remain straightforward. A slow or
  blocking dependency can still affect the process, and service extraction
  remains future work only when operational evidence justifies it.
