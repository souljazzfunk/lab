/**
 * Core domain types. Every other file speaks these. No module wire types appear here.
 */

// ---------- ids (branded so they cannot be swapped) ----------
type Brand<T, B extends string> = T & { readonly __brand: B };
export type CompanyId = Brand<string, "CompanyId">;
export type InvestigationId = Brand<string, "InvestigationId">;
export type ApprovalId = Brand<string, "ApprovalId">;
export type FindingId = Brand<string, "FindingId">;
export type ModuleId = Brand<string, "ModuleId">;
export type NodeId = Brand<string, "NodeId">;         // supply-chain graph node
/** sha256 over (moduleId, moduleVersion, atomKey, InputVersions). The unit of reuse. */
export type AtomKey = Brand<string, "AtomKey">;
/** Deterministic id for a launch = hash(moduleId, sorted AtomKeys). Doubles as module idempotency key. */
export type LaunchId = Brand<string, "LaunchId">;
export type UserRef = { id: string; display: string };
export type IsoCountry = Brand<string, "IsoCountry">; // "CD", "CN"
export type HsCode = Brand<string, "HsCode">;         // normalized 6-digit

// ---------- the supply chain graph (read-only input) ----------
export type NodeKind = "product" | "component" | "supplier" | "site" | "raw_material";
export interface NodeRef {
  id: NodeId;
  kind: NodeKind;
  tier: number;                         // 0 = company, 1..N
  /** 1.0 for confirmed tier-1; <1 for tiers estimated from trade stats. */
  existenceConfidence: number;
  country?: IsoCountry;
  hs?: HsCode[];
  label: string;
}

/**
 * Pins the exact inputs a module result depended on. Part of AtomKey, so a new graph
 * version or a new regulatory snapshot automatically misses the cache. Never compared by hand.
 *
 * `graph` is present only when the module's output depends on the company's graph (e.g.
 * procurement risk over suppliers). A module whose atoms are graph-independent (regulatory
 * intel over (country, HS)) omits it, so its atoms are shared across graph versions AND
 * companies; a graph-dependent atom is keyed by company, so results never cross tenants.
 */
export interface InputVersions {
  graph?: { companyId: CompanyId; version: string };
  /** Per upstream dataset the module declares it depends on, e.g. { "reg-db": "2026-09-20" }. */
  datasets: Readonly<Record<string, string>>;
}

/** Adapter-produced estimate for a set of atoms. Hours and money are both gated. */
export interface RunEstimate {
  hoursP50: number;
  hoursP90: number;
  costUsd: number;
}

// ---------- scope ----------
/**
 * The ONLY way to hold a scope a module will run on. Constructed solely by scope.resolve(),
 * so every scope is known to exist in a specific graph version (per encode-lessons-in-structure).
 */
declare const resolvedBrand: unique symbol;
export interface ResolvedScope {
  readonly [resolvedBrand]: true;     // not constructible outside scope.ts (brand never exported)
  graphVersion: string;
  /** Node -> inclusion confidence (existence x path confidence). Sorted by id for hashing. */
  nodes: ReadonlyMap<NodeId, number>;
  /** Human-readable, kept for the report ("cobalt, tiers 2-4, via 3 refiners"). */
  description: string;
}

/** What the user asked about, structured. UI pickers produce this directly; free text goes through extraction. */
export interface Focus {
  suppliers?: string[];       // names or ids, resolved against graph aliases
  regions?: string[];         // "DRC", "Xinjiang", ISO codes
  materials?: string[];       // "cobalt", "polysilicon", HS codes
  regulations?: RegulationTag[];
}
export type RegulationTag = "CBAM" | "US_TARIFF" | "EUDR" | "UFLPA" | "CSDDD" | (string & {});

// ---------- findings: the lingua franca between modules, planner and report ----------
/**
 * Every module's output is parsed by its adapter into Findings. The planner and report
 * see only these. Invariant: every Finding traces to exactly one atom of one module run.
 */
export interface Finding {
  id: FindingId;                       // hash(atomKey, adapter-local finding key): stable across replays
  source: Provenance;
  subjects: NodeId[];                  // which graph nodes it is about (non-empty)
  dimension: RegulationTag | "procurement" | "cost" | "deforestation" | (string & {});
  severity: "info" | "low" | "medium" | "high" | "critical";
  /** Module-reported confidence x min subject inclusion confidence. Computed, never LLM-written. */
  confidence: number;
  summary: string;                     // adapter-written, short, factual
  /** Named numeric facts the report may cite, e.g. { "tariff_cost_usd_yr": 1.2e6 }. */
  metrics: Readonly<Record<string, number>>;
  /** Module hints the planner may act on, e.g. "upstream refiners unassessed". Plain data. */
  leads?: string[];
}

export interface Provenance {
  moduleId: ModuleId;
  moduleVersion: string;
  atomKey: AtomKey;
  launchId: LaunchId;
  inputs: InputVersions;
  completedAt: string;
  reused: boolean;                     // true when this investigation did not pay for the run
}

// ---------- budget / human gates ----------
export interface Budget {
  maxCostUsd: number;                  // sum of estimated cost this investigation may commit
  autoApprove: { belowCostUsd: number; belowHoursP90: number }; // a wave under both skips approval
  maxWaves: number;                    // re-plan rounds; bounds agentic drift
}

export interface PendingApproval {
  kind: "approval";
  approvalId: ApprovalId;
  launches: Array<{ module: ModuleId; scope: string; estimate: RunEstimate; why: string }>;
  total: RunEstimate;
}
export interface PendingClarification {
  kind: "clarification";
  clarificationId: string;
  question: string;                    // "‘Supplier X’ matches 3 nodes - which?"
  /** matchScore = how well the term matched (resolution quality), kept apart from the node's own
   *  existenceConfidence (estimation quality). The UI shows both. */
  candidates: Array<{ node: NodeRef; matchScore: number }>;
}

export interface ModuleRunSummary {
  launchId: LaunchId; module: ModuleId; scope: string; state: RunState; estimate: RunEstimate; reused: boolean;
}
export type RunState = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export type InvestigationStatus =
  | "planning" | "awaiting_human" | "running" | "synthesizing" | "reported" | "cancelled" | "failed";

// ---------- report ----------
/**
 * Report invariant (encoded): every claim cites >=1 finding, and every number in prose is a
 * placeholder bound to a Finding metric. The LLM cannot emit a bare figure.
 */
export type NonEmpty<T> = [T, ...T[]];
export interface Claim {
  template: string;                                   // "Tariff exposure is {{a}} per year."
  figures: Record<string, { finding: FindingId; metric: string }>;
  cites: NonEmpty<FindingId>;
  confidence: number;                                 // min over cited findings; computed
}
export interface Report {
  question: string;
  audiences: Record<"procurement" | "esg" | "legal" | "exec", Claim[]>;
  gaps: string[];                                     // what was not assessed and why (declined, budget, failed)
  provenance: Provenance[];                           // deduplicated, for the appendix
  generatedFromEventSeq: number;                      // report is a pure function of the log up to here
}

// ---------- events: the single source of truth per investigation ----------
/**
 * Append-only per-investigation stream. State is a fold over this; nothing else is persisted
 * for an investigation. LLM outputs are recorded as events so replay never re-calls the LLM.
 */
export type InvestigationEvent =
  | { t: "opened"; req: OpenRequest; graphVersion: string; at: string } // graph pinned here
  | { t: "clarification_needed"; c: PendingClarification; at: string }
  | { t: "plan_proposed"; wave: number; proposal: PlanProposal; trace: PlannerTrace; at: string }
  | { t: "plan_rejected_steps"; wave: number; rejects: Array<{ step: number; reason: string }>; at: string }
  | { t: "launch_planned"; launch: PlannedLaunch; at: string }
  | { t: "human_input"; input: HumanInput; at: string }
  | { t: "launch_started"; launchId: LaunchId; at: string }
  /** From our own launch OR another investigation's launch we subscribed to. Keyed by atom, not launch. */
  | { t: "atoms_settled"; launchId: LaunchId; findings: Finding[]; settled: AtomKey[]; failed: AtomKey[]; at: string }
  | { t: "report_written"; report: Report; at: string }
  | { t: "failed"; reason: string; at: string };

/** Serializable form of ResolvedScope (the branded class is rebuilt on load via scope.rehydrate). */
export interface ResolvedScopeSnapshot { graphVersion: string; nodes: Array<[NodeId, number]>; description: string }

/**
 * Approvals are NOT stored as their own events: a pending approval is derived as
 * "launch_planned with gate=needs_approval and no matching approve/decline input".
 * ApprovalId = hash(investigationId, wave). One approval covers one wave.
 *
 * A launch the investigation wants. `atoms` is the set of atoms NOT already in the ledger;
 * `reusedAtoms` were found there and contribute findings at zero cost.
 */
export interface PlannedLaunch {
  launchId: LaunchId;
  module: ModuleId;
  wave: number;
  why: string;                         // planner's rationale, kept for audit
  scope: ResolvedScopeSnapshot;
  atoms: AtomKey[];                    // must be run (or joined, if another launch claims them first)
  reused: Finding[];                   // ledger hits at planning time; provenance.reused = true, cost 0
  estimate: RunEstimate;               // for `atoms` only
  gate: "auto" | "needs_approval";
}

// ---------- caller inputs (here, not in index.ts, so events don't import the API layer) ----------
export interface OpenRequest {
  requestId: string;             // caller-chosen idempotency key
  companyId: CompanyId;
  question: string;              // free text: "How exposed is our cobalt to UFLPA and EU CSDDD?"
  focus?: Focus;                 // optional structured hint from a UI picker (skips LLM mention extraction)
  budget: Budget;
  requestedBy: UserRef;
  trigger?: { kind: "user" } | { kind: "monitor"; alertId: string }; // monitoring can open investigations too
}

export type HumanInput =
  | { kind: "approve"; inputId: string; approvalId: ApprovalId; by: UserRef }
  | { kind: "decline"; inputId: string; approvalId: ApprovalId; by: UserRef; reason?: string }
  | { kind: "clarify"; inputId: string; clarificationId: string; answer: Focus; by: UserRef }
  | { kind: "follow_up"; inputId: string; question: string; by: UserRef }
  | { kind: "cancel"; inputId: string; by: UserRef };

// ---------- planner output (here so events can hold it without importing judgment.ts) ----------
/**
 * The small language the planner speaks for scope. Closed union, validated with a schema at
 * the judgment boundary; anything else is a rejected step, not a crash. Resolved in scope.ts.
 */
export type ScopeExpr =
  | { material: string }                                  // name or HS code
  | { supplier: string }                                  // name, alias, or NodeId
  | { region: string }                                    // country name/ISO, or sub-national ("Xinjiang")
  | { fromFindings: FindingId[] }                         // subjects of prior findings
  | { expand: ScopeExpr; direction: "upstream" | "downstream"; tiers: number }
  | { intersect: ScopeExpr[] }
  | { union: ScopeExpr[] }
  | { minConfidence: number; of: ScopeExpr };             // drop weakly-estimated nodes

export interface PlanProposal {
  steps: Array<{ module: ModuleId; scope: ScopeExpr; why: string }>;
  /** true => no further waves needed; synthesize once this wave settles. */
  done: boolean;
  /** Free text only for the audit timeline. Never parsed. */
  reasoning: string;
}

/** Audit record of one planner call: enough to reproduce or evaluate it later. */
export interface PlannerTrace {
  model: string;
  promptSha256: string;
  rawOutput: unknown;
  inputTokens: number;
  outputTokens: number;
}
