---
name: distributed-code-flow-diagrams
description: Generate scoped Mermaid diagrams for distributed code flows. Use when the user asks for a diagram, mental model, flow, lifecycle, protocol, who-does-what-when explanation, when analyzing a diff or before/after PR change, or when reasoning about replication, sharding, transactions, timestamps, or cross-node state.
---

# Distributed Code Flow Diagrams

## Purpose

Use this skill to explain confusing code by extracting the right actors in the algorithm and drawing them in the distributed context where correctness matters. Do not draw only the local call stack when the bug or invariant crosses replication, sharding, transaction, timestamp, or metadata boundaries.

## Core Rule

Start with the distributed boundary, then add local components.

- Replication: include the primary node and relevant primary components, the oplog or replicated log entry, and the secondary node with relevant apply components.
- Sharding: include `Mongos`, the primary or target shard, participant shards, and `ConfigServer` when routing, placement, metadata, coordinator state, or refresh is part of the flow.
- Transactions: include the parent transaction, side transaction if present, prepare, commit, abort, and visibility boundaries.
- Local-only flows: include only the components that own state transitions or payload transformations.

## Algorithm

1. Identify one anchor event.
   Example: `wildcard index becomes multikey inside a transaction`.

2. Classify the scope:
   - local only
   - replication
   - sharding
   - transaction
   - mixed, such as sharded transaction or replicated transaction metadata

3. Create required actor lanes before adding local details.
   - Replication lanes: `PrimaryNode`, `PrimaryIndexCatalog`, `Oplog`, `SecondaryApply`, `SecondaryIndexCatalog`.
   - Sharding lanes: `Mongos`, `CatalogCache`, `PrimaryShard`, `ParticipantShardA`, `ParticipantShardB`, `ConfigServer`.
   - Transaction lanes: `ParentTxn`, `SideTxn`, `CoordinatorShard`, `ParticipantShard`.

4. Add local components only where they explain ownership.
   Avoid dumping every function. Prefer components that author state, transmit state, reconstruct state, validate state, or persist state.

5. Track payloads explicitly.
   Examples: `multikeyPaths`, `multikeyMetadataKeys`, `setMultikeyMetadata`, `opTime`, `commitTimestamp`, `shardVersion`, `databaseVersion`, `routing metadata`.

6. Mark phase boundaries.
   Examples: `before prepare`, `side txn commit`, `parent abort`, `secondary apply`, `participant decision`, `metadata refresh`, `critical section`.

7. After the diagram, add a short explanation answering:
   - who authors the state
   - how it is transmitted
   - who reconstructs or derives it
   - what must match across actors

8. If analyzing a **diff** (PR, branch, before/after): use **one lifecycle** with inline `⛔ OLD` / `✅ NEW` notes — see [Diff analysis](#diff-analysis-one-lifecycle-with-inline-beforeafter) below. Do not use `rect rgb`, `box`, or `classDef` for coloring.

## Mermaid Choices

- Use `sequenceDiagram` for lifecycles, transactions, replication, and sharding protocols.
- Use `flowchart TD` for decision trees or single-node algorithms.
- Prefer 4-8 participants. If more are needed, split into multiple diagrams.
- Use Mermaid-safe node IDs: no spaces, no reserved keywords, no styling.

### Renderer compatibility (Cursor, GitHub, many IDEs)

Do **not** rely on Mermaid color styling — it is often stripped or unsupported:

- `rect rgb(...)` / `rect #hex` — box outline may render; **fill color usually does not**
- `box green ...` — often **not visible** (needs Mermaid ~11+)
- `classDef fill:...` / `linkStyle stroke:...` — **often stripped**

Use **structure + emoji labels** instead of color. For full-color output, suggest [mermaid.live](https://mermaid.live) or an exported image.

## Diff analysis: one lifecycle with inline before/after

Use this when the user asks to explain a **diff**, **PR change**, **before vs after**, or when you are reviewing what a branch changed in a distributed flow.

### Rules

1. Draw **one** `sequenceDiagram` — the **after** lifecycle as the main arrow flow. Do not split into separate before/after charts unless the user asks.
2. At each **changed** step, add a `Note over` with both sides:
   - `⛔ OLD: …` — removed or broken behavior
   - `✅ NEW: …` — what replaces it
3. Prefix **new/changed message arrows** with `✅` in the label. Leave unchanged steps unmarked.
4. Keep the same participants and phase order as a plain lifecycle diagram — only annotate what the diff touches.
5. After the diagram, add a short read-this-as paragraph covering: who authors state now, what changed in transmission/reconstruction, and what invariants must still match.

### Template

```mermaid
sequenceDiagram
    participant Client
    participant ParentTxn as Parent txn
    participant SideTxn as Side txn
    participant Index
    participant Oplog
    participant Secondary
    participant Planner

    Client->>ParentTxn: anchor event (unchanged — no emoji)

    Note over ParentTxn,Index: ⛔ OLD: …<br/>✅ NEW: …

    ParentTxn->>SideTxn: ✅ new or changed step
    SideTxn->>Index: ✅ …
    SideTxn->>Oplog: ✅ …
    Note over SideTxn,Oplog: ⛔ OLD: … (only if arrow label alone is not enough)

    Client->>Planner: downstream read or apply (unchanged trigger)

    Note over Planner,Index: ⛔ OLD: …<br/>✅ NEW: …
    Planner->>Index: ✅ changed step

    Oplog->>Secondary: apply (unchanged trigger)
    Secondary->>Index: ✅ changed step
    Note over Secondary,Index: ⛔ OLD: …
```

### Example: diff lifecycle (wildcard multikey in txn)

```mermaid
sequenceDiagram
    participant Client
    participant ParentTxn as Parent txn
    participant SideTxn as Side txn
    participant Index as Wildcard index
    participant Oplog
    participant Secondary
    participant Planner

    Client->>ParentTxn: insert {a:[1,2]}
    ParentTxn->>ParentTxn: keygen finds path "a" is multikey

    Note over ParentTxn,Index: ⛔ OLD: parent txn inserted metadata keys here<br/>✅ NEW: parent txn does NOT insert keys (side txn does)

    ParentTxn->>SideTxn: open side txn
    SideTxn->>Index: ✅ insert metadata key for "a"
    SideTxn->>SideTxn: ✅ set catalog isMultikey
    SideTxn->>Oplog: ✅ setMultikeyMetadata paths=["a"]
    Note over SideTxn,Oplog: ⛔ OLD: oplog had btree paths (empty for wildcard)
    SideTxn->>SideTxn: ✅ commit now — before parent commits
    SideTxn->>ParentTxn: ✅ hasSideCommittedWildcardKeys = true

    Client->>Planner: find in same txn

    Note over Planner,Index: ⛔ OLD: scan parent snapshot only — missed side commit<br/>✅ NEW: RYOW — union both scans
    Planner->>Index: ✅ scan parent RU (empty for side keys)
    Planner->>Index: ✅ scan fresh side RU (sees "a")
    Planner->>Planner: ✅ union → plan as multikey

    Client->>ParentTxn: commit or abort

    Oplog->>Secondary: apply setMultikeyMetadata
    Secondary->>Index: ✅ regenerate KeyString + insert "a"
    Note over Secondary,Index: ⛔ OLD: secondary updated catalog only — no keys in index
```

Read this as: the diff moves metadata key authorship from the parent txn to an immediate side txn, changes the oplog payload format for wildcards, adds a dual-RU read path for RYOW, and makes secondaries reconstruct and insert keys instead of updating catalog alone.

## Example: Non-Transaction Multikey Replication

```mermaid
sequenceDiagram
    participant PrimaryWrite
    participant PrimaryIndex
    participant PrimaryStorage
    participant Oplog
    participant SecondaryApply
    participant SecondaryIndex
    participant SecondaryStorage

    PrimaryWrite->>PrimaryIndex: Insert or update document
    PrimaryIndex->>PrimaryIndex: Key generation discovers multikeyness
    PrimaryIndex->>PrimaryStorage: Persist catalog paths or wildcard metadata keys
    PrimaryWrite->>Oplog: Replicate user write
    Oplog->>SecondaryApply: Apply user write
    SecondaryApply->>SecondaryIndex: Re-run key generation
    SecondaryIndex->>SecondaryStorage: Persist same kind of multikey metadata
```

Read this as: primary and secondary both derive multikeyness from the same user write. The oplog carries the write, not a separate metadata event.

## Example: Transaction Side Metadata

```mermaid
sequenceDiagram
    participant PrimaryParentTxn
    participant PrimarySideTxn
    participant PrimaryStorage
    participant Oplog
    participant SecondaryApply
    participant SecondaryStorage

    PrimaryParentTxn->>PrimaryParentTxn: User write discovers metadata side effect
    PrimaryParentTxn->>PrimarySideTxn: Request metadata update
    PrimarySideTxn->>PrimaryStorage: Commit metadata independently
    PrimarySideTxn->>Oplog: Write metadata oplog entry
    Oplog->>SecondaryApply: Apply metadata oplog entry
    SecondaryApply->>SecondaryStorage: Materialize metadata side effect
    PrimaryParentTxn->>Oplog: Later commit or abort parent txn
```

Read this as: the side transaction is independent of the parent. If it commits, the secondary should apply the side-effect metadata event even if the parent later aborts.

## Example: Sharding Versioning Protocol

```mermaid
sequenceDiagram
    participant Client
    participant Mongos
    participant CatalogCache
    participant PrimaryShard
    participant ParticipantShard
    participant ConfigServer

    Client->>Mongos: Send sharded read or write
    Mongos->>CatalogCache: Get routing table and versions
    CatalogCache-->>Mongos: Target shards plus shardVersion and databaseVersion
    Mongos->>PrimaryShard: Command with shardVersion and databaseVersion
    Mongos->>ParticipantShard: Command with shardVersion and databaseVersion

    alt Shard metadata is current
        PrimaryShard-->>Mongos: OK
        ParticipantShard-->>Mongos: OK
        Mongos-->>Client: Return result
    else Shard detects stale version
        ParticipantShard-->>Mongos: StaleConfig or StaleDbVersion
        Mongos->>CatalogCache: Mark stale and refresh routing metadata
        CatalogCache->>ConfigServer: Fetch latest placement and versions
        ConfigServer-->>CatalogCache: Refreshed metadata
        CatalogCache-->>Mongos: New targets and versions
        Mongos->>PrimaryShard: Retry with refreshed versions
        Mongos->>ParticipantShard: Retry with refreshed versions
    end
```

Read this as: `Mongos` owns targeting, `CatalogCache` owns the router's placement/version view, and shards validate `shardVersion` and `databaseVersion`. `StaleConfig` and `StaleDbVersion` are protocol signals to refresh and retry.

## Example: Distributed Transaction Commit

```mermaid
sequenceDiagram
    participant Client
    participant Mongos
    participant CoordinatorShard
    participant ParticipantShardA
    participant ParticipantShardB

    Client->>Mongos: commitTransaction
    Mongos->>CoordinatorShard: Start commit coordination
    CoordinatorShard->>ParticipantShardA: prepareTransaction
    CoordinatorShard->>ParticipantShardB: prepareTransaction
    ParticipantShardA-->>CoordinatorShard: voteCommit with prepareTimestamp
    ParticipantShardB-->>CoordinatorShard: voteCommit with prepareTimestamp
    CoordinatorShard->>CoordinatorShard: Persist commit decision
    CoordinatorShard->>ParticipantShardA: commitTransaction
    CoordinatorShard->>ParticipantShardB: commitTransaction
    CoordinatorShard-->>Mongos: commit acknowledged
    Mongos-->>Client: commitTransaction OK
```

Read this as: once the coordinator persists the decision, recovery must drive every participant to that same decision.

## Example: Resharding Phase Machine

```mermaid
sequenceDiagram
    participant Mongos
    participant ConfigServerCoordinator
    participant DonorShard
    participant RecipientShard
    participant ConfigServerCatalog

    Mongos->>ConfigServerCoordinator: reshardCollection
    ConfigServerCoordinator->>DonorShard: Start donating
    ConfigServerCoordinator->>RecipientShard: Create temporary collection
    RecipientShard->>DonorShard: Clone existing data
    DonorShard->>RecipientShard: Stream writes during clone
    RecipientShard-->>ConfigServerCoordinator: Caught up
    ConfigServerCoordinator->>DonorShard: Enter critical section
    ConfigServerCoordinator->>ConfigServerCatalog: Commit new placement metadata
    ConfigServerCoordinator->>RecipientShard: Rename temp collection
    ConfigServerCoordinator->>DonorShard: Drop old collection data
```

Read this as: resharding is a coordinator-owned phase machine. Donors own old data, recipients own clone/apply, and config metadata commit changes routing.
