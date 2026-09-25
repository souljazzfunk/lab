/**
 * The contract each business module team (or we, on their behalf) implements, plus the
 * content-addressed run ledger shared across all investigations.
 *
 * Key idea: modules are deduplicated on their PROJECTED INPUT ATOMS, not on the question
 * or the scope. "Cobalt" and "DRC" both project to (CD, 8105.20) for the regulatory module,
 * so the second investigation reuses the first's atom for free.
 */
import type {
  AtomKey, CompanyId, Finding, InputVersions, InvestigationId, LaunchId, ModuleId, NodeKind,
  ResolvedScope, RegulationTag, RunEstimate,
} from "./domain";
import type { GraphSnapshot } from "./scope";

/**
 * One adapter per module. Generic over the module's own Atom and wire Output; neither type
 * escapes this interface (callers hold ModuleAdapter<any, any> and only see Finding).
 */
export interface ModuleAdapter<Atom, WireOutput> {
  id: ModuleId;
  version: string;                     // bump => all prior atoms miss the ledger

  /** Shown to the planner verbatim. What it answers, what scope it wants, rough cost. Keep short. */
  card: {
    purpose: string;                   // "Per (country, HS) regulatory exposure under CBAM/tariffs/EUDR/UFLPA"
    covers: RegulationTag[] | "procurement" | "cost" | (string & {});
    scopeHint: string;                 // "materials or regions; operates on country x HS pairs"
    typicalHours: number;
    /** Checked deterministically before project(): a step whose scope has none of these is rejected. */
    acceptsNodeKinds: readonly NodeKind[];
  };

  /**
   * Scope -> the module's unit of work. Pure. This is where heterogeneity lives: the
   * regulatory module projects nodes to (country, HS) pairs; procurement risk projects to
   * supplier nodes; a whole-input module returns exactly one atom.
   * Invariant: atoms are canonical (same meaning => same `key`).
   */
  project(scope: ResolvedScope, graph: GraphSnapshot): Array<{ key: string; atom: Atom }>;

  /**
   * Which inputs the result will depend on, resolved NOW (part of AtomKey). Include `graph` only if
   * the output depends on the company graph; omit it to share atoms across companies and versions.
   */
  currentInputs(graph: { companyId: CompanyId; version: string }): Promise<InputVersions>;

  /** How long a cached atom stays valid even if versions match (regulations move). */
  maxAgeDays: number;

  estimate(atoms: Atom[]): RunEstimate;

  /** Start the module. MUST be idempotent on launchId (passed to the module as its idempotency key). */
  launch(launchId: LaunchId, atoms: Atom[], inputs: InputVersions): Promise<void>;

  /** Poll path. Webhook path goes through parseCallback. Both converge on `settle`. */
  poll(launchId: LaunchId): Promise<{ done: false } | { done: true; output: WireOutput }>;
  parseCallback(raw: unknown): { launchId: LaunchId; output: WireOutput } | null;

  /** Best-effort. Called by the ledger when a launch loses its last subscriber. */
  cancel?(launchId: LaunchId): Promise<void>;

  /**
   * Wire -> domain. The ONLY place WireOutput is read. Must attribute each finding to the atom
   * it came from (so the ledger can store per-atom) and report atoms the module failed on.
   */
  toFindings(output: WireOutput, atoms: Array<{ key: string; atom: Atom }>): {
    perAtom: Map<string, Array<Omit<Finding, "id" | "source" | "confidence"> & { moduleConfidence: number }>>;
    failed: string[];
  };
}

export function atomKey(m: ModuleAdapter<any, any>, key: string, inputs: InputVersions): AtomKey {
  // sha256(JSON.stringify([m.id, m.version, key, inputs.graph ?? null, sortedEntries(inputs.datasets)]))
  throw new Error("not implemented");
}

export function launchIdFor(module: ModuleId, atoms: AtomKey[]): LaunchId {
  // sha256(module + sorted(atoms).join()) - the same missing-atom set always yields the same launch
  throw new Error("not implemented");
}

/**
 * Global, cross-investigation ledger. The ONLY shared mutable state in the system.
 *
 * Concurrency rule (per separate-before-serializing-shared-state): an atom row is created by
 * `claim` with insert-if-absent; the first claimer's launchId owns it. Later claimers get
 * "in_flight" and simply subscribe. Settlement is written once per launch by whichever worker
 * observes completion first (conditional update on state='running'); a second writer is a no-op.
 * Investigations never write here directly; they receive `atoms_settled` events via fan-out.
 */
export interface RunLedger {
  /** For each atom: done (with findings), in flight (by which launch), or free to claim. */
  lookup(keys: AtomKey[], maxAgeDays: number): Promise<Map<AtomKey, LedgerEntry>>;
  /** Insert-if-absent for each atom. Returns the atoms this launch actually owns. */
  claim(launchId: LaunchId, keys: AtomKey[]): Promise<{ owned: AtomKey[]; inFlightElsewhere: Map<AtomKey, LaunchId> }>;
  subscribe(launchId: LaunchId, investigation: InvestigationId): Promise<void>;
  /**
   * On cancel. Returns the remaining subscriber count; at 0 the runtime calls adapter.cancel and
   * releases the atoms (state -> absent), so no module keeps running for nobody.
   */
  unsubscribe(launchId: LaunchId, investigation: InvestigationId): Promise<number>;
  /** Idempotent. Returns subscribers to notify. */
  settle(launchId: LaunchId, findings: Map<AtomKey, Finding[]>, failed: AtomKey[]): Promise<InvestigationId[]>;
  /** Failed atoms are released so a later plan may retry them (bounded by attempts). */
}
export type LedgerEntry =
  | { state: "done"; findings: Finding[]; completedAt: string }
  | { state: "in_flight"; launchId: LaunchId }
  | { state: "absent" }
  | { state: "failed"; attempts: number };
