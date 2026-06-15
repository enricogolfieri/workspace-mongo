---
name: code-flow-scope-colors
description:
  Adds reusable scope-based color labels to MongoDB code-flow explanations. Diagrams must use
  abstract assignment notation (colored lhs = rhs, gates, scope open/close) for every flow—not only
  oplog timestamps. Use for OperationContext, WUOW, RecoveryUnit, oplog, catalog, routing, yield,
  acquisition, multikey, or any scope boundary.
---

# Code Flow Scope Colors

## Mandatory Output Rule

**Every response using this skill MUST:**

1. Begin with an **Adapted Scope Palette** (only colors used in this flow).
2. Include **abstract assignment blocks** (`coloredField = expr`, gates, scope open/close) for the
   whole flow — not only timestamp or oplog sections.
3. End with the **Invariant Prompt**.

Do not dump the full canonical palette unless all nine colors appear. Never assign a color without
saying what scope it denotes. Never explain a flow with call names and arrows alone.

## Core Rule

Color by **owning scope / lifetime**, not by function name or call site.

**Diagrams are abstract assignment code**, not narrated call graphs. Show what gets stored where,
with `=` for every mutation or scope crossing. Use `->` only for sequencing (open WUOW, then
commit), never as a substitute for `dest = source`.

**Do not color a function call** unless you are naming the scope it establishes. Prefer the state
the call creates:

```text
// Wrong
⚪ acquireCollection() -> applyOperation_inlock()

// Right
🟢 TransactionResources += CollectionAcquisition request   // extends 🟢 opCtx bundle
⚪ collHandle = view into 🟢 TransactionResources           // stack-local ref
```

## Canonical Scope Palette

Reference definitions. Copy only the entries you use into the Adapted Scope Palette and adjust
wording when the flow needs a sharper label.

```text
⚫ black  = durable/on-disk state
           RecordStore bytes, SortedDataInterface entries, _mdb_catalog records,
           durable oplog records, persisted config collections.

🔴 red    = in-memory catalog / metadata view
           CollectionCatalog, IndexCatalog, IndexCatalogEntry, CollectionPtr metadata,
           in-memory multikey state, in-memory routing-independent catalog metadata.

🟡 yellow = oplog / replicated payload
           OplogEntry, DurableOplogEntry, applyOps payload, prepare/commit oplog entries,
           op.timestamp, op.object, op.nss, op.uuid.

🟢 green  = OperationContext scope and opCtx decorations
           MultikeyPathTracker, Locker, CurOp, RecoveryUnit access through opCtx,
           TransactionResources, OperationShardingState, request-local state
           attached to the current operation.

🟠 orange = ServiceContext / process-global service scope and decorations
           StorageEngine, ReplicationCoordinator, OpObserver, global services,
           server-wide feature flags, failpoints, service-level registries,
           CursorManager stashed resources.

⚪ white  = WriteUnitOfWork / local lexical scope
           WUOW lifetime, variables created inside the WUOW, rollback hooks,
           scoped guards, stack-local temporaries, per-WUOW derived state.
           NOT opCtx decorations, NOT acquisition handles, NOT API entry points.

🟣 purple = RecoveryUnit / storage transaction in-memory state
           RU timestamp, commit timestamp, prepare timestamp, snapshot state,
           WiredTiger transaction state before durability.

🟤 brown  = routing / sharding / placement metadata
           ShardVersion, DatabaseVersion, ChunkManager, CatalogCache,
           placement info, routing table state, ownership filter, RangePreserver.

🔵 blue   = client request / command payload before it becomes oplog
           InsertCommandRequest, UpdateRequest, DeleteRequest, parsed command,
           query specs, update specs, router-attached version fields.
```

## Adapted Scope Palette

Build this at the top of every response. Include only colors used below. Extend or narrow canonical
definitions when the flow requires it.

Example for shard-role acquisition:

```text
Adapted palette (shard role acquisition):

🔵  Incoming command + router-attached ShardVersion / DatabaseVersion
🟢  OperationContext decorations: OperationShardingState, TransactionResources,
    locks; CollectionAcquisition is a ref-counted view into this scope
🔴  In-memory local catalog snapshot: CollectionCatalog, CollectionPtr
🟤  Sharding placement: PlacementConcern, ownership filter, RangePreserver
🟣  Storage snapshot opened to match the catalog read
⚫  Durable bytes read/written through the pinned catalog view
⚪  WriteUnitOfWork wrapping individual document writes (separate from acquisition)
```

## Assignment & Scope-Change Notation (mandatory — all flows)

**Every diagram** for any topic (oplog, yield, acquisition, multikey, sharding, commands) must use
this notation. Specialized sections below are **templates**, not exceptions.

### Required elements

| Element           | Syntax                                           | When                                                |
| ----------------- | ------------------------------------------------ | --------------------------------------------------- |
| Copy / promote    | `🟢 dst = 🟡 src`                                | Value crosses scope; recolor on RHS if type changes |
| In-place mutate   | `🔴 entry.flags \|= MULTIKEY`                    | Field updated inside same scope                     |
| Gate              | `canX = false — because <scope condition>`       | Branch chooses which assignments run                |
| Conditional write | `if canX: 🟣 field = expr`                       | Write may be skipped; say who owns it when false    |
| Scope open        | `⚪ wuow = WriteUnitOfWork { open }`             | New lexical lifetime                                |
| Scope close       | `⚪ wuow.commit()` / `destroy`                   | End lifetime; show what 🟣/⚫ gains                 |
| Detach            | `⚪ bundle = 🟢 resources; 🟢 resources = empty` | Ownership leaves opCtx                              |
| Attach            | `🟢 resources = ⚪ bundle`                       | Restore                                             |
| Derive            | `🟡 subOpᵢ = extract(🟡 parent)`                 | New objects in same or new scope                    |
| Invalidate        | `🔴 CollectionPtr = UNSAFE`                      | Handle outlives valid view                          |

### Forbidden (any flow)

- Arrows with no `=` when something is **stored** (`🟡 ts -> 🟣` alone)
- `[when …]` / `[if needed]` without naming the gate and alternate owner
- Bare API names as steps (`acquireCollection`, `setMultikey`, `yield`)
- Coloring a function instead of the state it reads/writes
- Prose paragraphs that repeat the diagram

### Abstract shapes (reuse in every flow)

**Copy across scopes:**

```text
🟢 MultikeyPathTracker.currentOpTimestamp = 🟡 OplogEntry.timestamp
```

**Gate + conditional write:**

```text
canStampStorageTxn = <bool expr with colored operands>
if canStampStorageTxn:
    🟣 RecoveryUnit.commitTimestamp = <🟡 or ⚪ expr>
else:
    🟣 RecoveryUnit.commitTimestamp = <unchanged | owned by ⚪ outer / other path>
```

**Scope lifetime:**

```text
⚪ wuow = WriteUnitOfWork { open }
<assignments and writes inside ⚪>
⚪ wuow.commit()   — commits 🟣 txn → visible as ⚫
```

**Detach / attach (yield, stash):**

```text
⚪ yielded = 🟢 TransactionResources
🟢 TransactionResources = detached
🔴 CollectionPtr = UNSAFE
🟣 RecoveryUnit = no active snapshot
// restore:
🟢 TransactionResources = ⚪ yielded
🔴 CollectionPtr = restored view
```

### Checklist before finishing a diagram

- [ ] Every scope boundary crossed has an explicit `=` line
- [ ] Every gate has `= true/false` and the failing branch’s owner
- [ ] Every ⚪/🟢/🟣 open/close shown as assignment or `destroy`, not implied
- [ ] No step is only a function name

---

## Reference Patterns (templates — use what the flow needs)

Copy the blocks that apply. Combine multiple blocks in one diagram (e.g. extract + apply +
multikey).

### Oplog apply — storage commit timestamp

Use when: secondary apply, `applyOperation_inlock`, extracted `applyOps`,
`RecoveryUnit::setTimestamp`.

### Gate

```text
assignOperationTimestamp =
    if 🟢 opCtx.writesAreReplicated == true     → false
    else if ⚪ Locker.inAWriteUnitOfWork == true → false
    else if 🟠 ReplicationCoordinator.isReplSet  → true
    else if recoveringMode                     → true
    else                                       → false
```

| Branch                | Meaning                                                              |
| --------------------- | -------------------------------------------------------------------- |
| `writesAreReplicated` | Primary / user write: 🟡 `ts` applied when oplog is logged, not here |
| `inAWriteUnitOfWork`  | Nested inside outer ⚪ WUOW (e.g. prepare): outer scope owns 🟣 ts   |
| `isReplSet`           | Normal secondary steady-state apply                                  |
| `recoveringMode`      | Standalone recovery from oplog                                       |

### Timestamp source (copy exactly this)

```text
🟡 opTs = OplogEntry.timestamp
🟡 applyOpsTs = OplogEntry.applyOpsTimestamp    // parent ts stamped at extract

timestamp =
    if groupedContainerOpsFromApplyOps → applyOpsTs ?? opTs
    else                               → opTs
```

### Conditional write to 🟣 (copy exactly this)

```text
if assignOperationTimestamp && timestamp != null:
    🟣 RecoveryUnit.commitTimestamp = timestamp    // [from 🟡]
else:
    — no 🟣 assignment at this site; see ⚪ outer WUOW or oplog log path
```

### Full chain: secondary extracted applyOps sub-op (CRUD)

```text
🟡 parentApplyOps.timestamp
  — one replicated command entry
  -> extract
      🟡 subOp.timestamp = parentApplyOps.timestamp     // unless sub-op overrides
      🟡 subOp.applyOpsTimestamp = parentApplyOps.timestamp

// per subOp (worker apply)
🟢 MultikeyPathTracker.currentOpTimestamp = 🟡 subOp.timestamp
  — multikey side channel; NOT the same field as 🟣 commitTimestamp

assignOperationTimestamp = true
  — 🟢 writesAreReplicated == false; ⚪ inAWriteUnitOfWork == false; 🟠 isReplSet

timestamp = 🟡 subOp.timestamp

⚪ wuow = WriteUnitOfWork { open }
if assignOperationTimestamp:
    🟣 RecoveryUnit.commitTimestamp = timestamp
⚫ RecordStore / indexes written under 🟣 txn
⚪ wuow.commit()
```

### Full chain: gate false (prepared / wrapping WUOW)

```text
assignOperationTimestamp = false
  — because ⚪ Locker.inAWriteUnitOfWork == true

timestamp = 🟡 op.timestamp
  — still parsed; may be ignored for 🟣 at this site

⚪ wrappingWUOW { … inner applies … }
  — inner ops do NOT execute: 🟣 RecoveryUnit.commitTimestamp = timestamp
🟣 commitTimestamp = <set by outer ⚪ / prepare commit path, not per inner 🟡>
```

### Full chain: gate false (primary / replicated write)

```text
assignOperationTimestamp = false
  — because 🟢 opCtx.writesAreReplicated == true

🟡 op.timestamp
  — present on command but not copied to 🟣 at applyOperation_inlock
🟣 commitTimestamp = <from oplog logging / slot, not this apply path>
```

### Oplog apply — multikey side channel (separate from 🟣 commit ts)

```text
🟢 MultikeyPathTracker.currentOpTimestamp = 🟡 OplogEntry.timestamp
  — per op while 🟢 tracker.isTracking == true
// after batch on worker:
🟢 paths = MultikeyPathTracker.getMultikeyPathInfo()
🔴 IndexCatalogEntry.earliestTimestamp = min(🔴 existing, 🟢 currentOpTimestamp per path)
🔴 IndexCatalogEntry.paths \|= 🟢 paths
// catalog flush (later):
🟣 RecoveryUnit.commitTimestamp = 🔴 earliestTimestamp
⚫ _mdb_catalog index metadata durable
```

### applyOps extract (secondary terminal)

```text
🟡 parent = OplogEntry { applyOps: [ … ] }
⚪ derivedOps = []
for each element in parent.applyOps:
    🟡 subOp = merge(parent common fields, element)
    🟡 subOp.applyOpsTimestamp = 🟡 parent.timestamp
    🟡 subOp.applyOpsIndex = i
    ⚪ derivedOps += 🟡 subOp
// parent 🟡 not applied as one unit; each ⚪ derivedOps entry → worker queue
```

### Collection acquisition (read/write path)

```text
🟢 TransactionResources.locks += { nss, MODE_IX }
🔴 collPtr = CollectionCatalog.lookup(nss | uuid)
🟢 TransactionResources.catalogView = 🔴 collPtr
🟣 RecoveryUnit.snapshot = open_for(🔴 collPtr)
⚪ collHandle = ref(🟢 TransactionResources)   // stack view only
```

### Transaction yield

```text
🟢 savedLocks = Locker.getHeldLocks()
🟢 Locker.heldLocks = {}
🔴 CollectionPtr = UNSAFE
🟣 RecoveryUnit.snapshot = none
⚪ yieldedBundle = 🟢 TransactionResources
🟢 TransactionResources = detached
⚪ collHandle = INVALID
```

### Sharding — command to durable placement

```text
🔵 cmd.shardVersion = routerAttached
🟤 placementFilter = CatalogCache.getChunkRangeFor(🔵 nss)
🟢 OperationShardingState.versions = 🔵 cmd versions
🟢 OperationShardingState.filter = 🟤 placementFilter
🔴 catalogEntry = CollectionCatalog.lookup(🔵 nss)
if cmd mutates placement:
    ⚪ wuow = WriteUnitOfWork { open }
    🟣 RecoveryUnit.commitTimestamp = <routing update ts>
    ⚫ config.chunks / placement collection update
    ⚪ wuow.commit()
```

### Primary insert (contrast — no 🟣 stamp at apply)

```text
🔵 insertDoc = client payload
🟢 opCtx.writesAreReplicated = true
canStampStorageTxn = false   — 🟢 writesAreReplicated
⚪ wuow = WriteUnitOfWork { open }
⚫ RecordStore.insert(🔵 doc)
🟡 oplogSlot = logOplog(…)     — 🟡 ts assigned here, not at applyOperation_inlock
⚪ wuow.commit()
```

## Drawing Style — Annotated Schema

Prefer indented text diagrams over Mermaid. Mermaid colors are often stripped in Cursor and GitHub.

**The diagram IS the explanation.** Keep the colored schema shape, but every step gets a short
inline note (`— …`) saying what happens and why. No separate prose blocks that repeat the diagram.

Format: **assignment block(s) first**, then optional `->` sequencing with `—` notes.

```text
🟢 savedLocks = Locker.heldLocks
🟢 Locker.heldLocks = {}
🔴 CollectionPtr = UNSAFE
  — catalog view no longer valid without snapshot
-> ⚪ yieldedBundle = 🟢 TransactionResources
   🟢 TransactionResources = detached
  — caller holds bundle until restore; ⚪ collHandle invalid
```

Rules:

- Color the **state**, not the bare function name.
- **Every stored value** = `lhs = rhs` before `->`.
- Gates: `name = true/false — because <condition>`.
- `->` = time order only; never the only representation of a copy.
- One `—` note per sequenced block (optional).
- Pull in **Reference Patterns** that match the flow (not only oplog timestamp).

Good (yield — assignments throughout):

```text
🟢 savedLocks = Locker.heldLocks
🟢 Locker.heldLocks = {}
🔴 CollectionPtr = UNSAFE
🟣 RecoveryUnit.snapshot = none
⚪ yieldedBundle = 🟢 TransactionResources
🟢 TransactionResources = detached
⚪ collHandle = INVALID
```

Bad:

```text
🟢 opCtx -> yield -> ⚪ YieldedTransactionResources
yieldTransactionResourcesFromOperationContext()
🔴 CollectionPtr -> UNSAFE
```

## Source Notes

Prefer explicit RHS on the same line instead of `[from …]` when space allows:

```text
⚪ InsertStatement.oplogSlot = OpTime(🟡 op.timestamp, 🟡 op.term)
⚪ BsonRecord.ts = ⚪ InsertStatement.oplogSlot.getTimestamp()
🟢 MultikeyPathTracker.currentOpTimestamp = ⚪ BsonRecord.ts
```

## Common Misassignments

Avoid these — they confuse scope with call site:

| Thing                   | Wrong               | Right                                                                                    |
| ----------------------- | ------------------- | ---------------------------------------------------------------------------------------- |
| `acquireCollection()`   | ⚪ "local API call" | Operates on 🟢 opCtx; creates/extends 🟢 TransactionResources                            |
| `CollectionAcquisition` | ⚪ or unlabeled     | 🟢 view into TransactionResources; ⚪ only if describing the stack-local handle variable |
| `TransactionResources`  | ⚪                  | 🟢 opCtx decoration                                                                      |
| `WriteUnitOfWork`       | 🟢                  | ⚪ WUOW lexical scope                                                                    |
| `CursorManager` stash   | 🟢                  | 🟠 service-global cursor state crossing opCtx boundaries                                 |

## MongoDB Examples

Secondary oplog application (single CRUD op):

```text
🟢 MultikeyPathTracker.currentOpTimestamp = 🟡 OplogEntry.timestamp

assignOperationTimestamp = true
timestamp = 🟡 OplogEntry.timestamp

⚪ wuow = WriteUnitOfWork { open }
if assignOperationTimestamp:
    🟣 RecoveryUnit.commitTimestamp = timestamp
⚫ RecordStore / index writes
🔴 multikey paths recorded from 🟢 tracker
⚪ wuow.commit()
```

Prepared transaction apply:

```text
🟢 MultikeyPathTracker.currentOpTimestamp = 🟡 op.timestamp

assignOperationTimestamp = false
  — ⚪ Locker.inAWriteUnitOfWork == true

⚪ wrappingWUOW { open }
  — inner applies: no 🟣 RecoveryUnit.commitTimestamp = 🟡 op.timestamp per op
🔴 setMultikey uses 🟢 tracker
⚫ durable at prepare/commit boundary
🟣 commitTimestamp = <outer ⚪ / prepare path>
```

Secondary terminal applyOps (extracted sub-ops):

```text
🟡 parentApplyOps.timestamp
  -> extract:
      🟡 subOp.applyOpsTimestamp = 🟡 parentApplyOps.timestamp
      🟡 subOp.timestamp = 🟡 parentApplyOps.timestamp   // unless sub-op has own ts

// each subOpᵢ on a worker:
🟢 MultikeyPathTracker.currentOpTimestamp = 🟡 subOp.timestamp

assignOperationTimestamp = true
timestamp = 🟡 subOp.timestamp

⚪ wuow = WriteUnitOfWork { open }
if assignOperationTimestamp:
    🟣 RecoveryUnit.commitTimestamp = timestamp
⚫ writes for subOpᵢ only
⚪ wuow.commit()
```

Sharding/routing:

```text
🔵 cmd.shardVersion = routerAttached
🟤 filter = CatalogCache.chunkRangeFor(🔵 nss)
🟢 OperationShardingState.shardVersions = 🔵 cmd.shardVersion
🟢 OperationShardingState.ownershipFilter = 🟤 filter
🔴 entry = CollectionCatalog.lookup(🔵 nss)
if cmd mutates placement:
    ⚪ wuow = WriteUnitOfWork { open }
    ⚫ placement/config collections updated
    ⚪ wuow.commit()
```

## Response Structure

Use this order every time:

1. **Adapted Scope Palette** — only colors used in this flow
2. **Abstract assignment blocks** — Reference Patterns + flow-specific `=` lines (gates, copies,
   detach, derive, invalidate)
3. **Annotated schema** — same assignments in execution order; `->` only for sequencing; brief `—`
   notes
4. **Invariant Prompt** — 5 lines max

Step 2 is **required for every topic** (yield, acquisition, multikey, sharding, commands, oplog) —
not only 🟣 timestamps.

## Invariant Prompt

After drawing, briefly state:

```text
State author:
Transmission boundary:
Reconstruction/derivation point:
Durable effect:
What must match across scopes:
```
