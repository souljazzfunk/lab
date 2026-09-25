/**
 * Public surface of the orchestration layer. Everything a caller (web app, Slack bot,
 * monitoring trigger, worker process) needs is here. Module wire formats, the event log,
 * LLM prompts and the run ledger are NOT exported.
 *
 * Module map (call chain never exceeds: runtime -> investigation (pure) -> modules|judgment):
 *   index.ts          public API: createOrchestrator, Orchestrator, HumanInput, InvestigationView
 *   domain.ts         core types: ids, graph refs, Scope, Finding, InputVersions, events, state
 *   scope.ts          ScopeExpr DSL (what the planner may say) + deterministic resolver against the graph
 *   modules.ts        ModuleAdapter contract (one per business module) + content-addressed RunLedger
 *   investigation.ts  PURE decider: evolve(state, event) / decide(state, now) -> Effect[]; cost gate
 *   judgment.ts       the only two LLM calls: propose next plan wave, write report (numbers injected, not written)
 *   runtime.ts        thin shell: event store, leases, effect execution, wake-ups
 */
import type {
  InvestigationId, Budget, InvestigationStatus, Finding, ModuleRunSummary,
  PendingApproval, PendingClarification, Report, OpenRequest, HumanInput,
} from "./domain";
import type { ModuleAdapter } from "./modules";
import type { EventStore, GraphSource, WakeQueue } from "./runtime";
import type { JudgmentConfig } from "./judgment";

export interface OrchestratorDeps {
  store: EventStore;            // durable, append-only, optimistic concurrency per stream
  wake: WakeQueue;              // durable delayed-delivery queue (SQS / pg-boss / Cloud Tasks)
  graph: GraphSource;           // read-only access to the completed multi-tier analysis, versioned
  modules: readonly ModuleAdapter<any, any>[]; // registry; adding a module = adding an adapter
  judgment: JudgmentConfig;     // Claude model ids, token budgets
}

export function createOrchestrator(deps: OrchestratorDeps): Orchestrator {
  throw new Error("not implemented");
}

export interface Orchestrator {
  /**
   * Open (or re-open) an investigation. Idempotent on `requestId`: calling twice returns the
   * same InvestigationId and appends nothing. Returns immediately; planning happens on a worker.
   */
  open(req: OpenRequest): Promise<InvestigationId>;

  /** Everything a UI or bot needs to render "check back hours later". Derived from the event log. */
  view(id: InvestigationId): Promise<InvestigationView>;

  /**
   * All human input goes through one door: approvals, declines, clarifications, follow-up
   * questions, cancel. Idempotent on `input.inputId`.
   */
  send(id: InvestigationId, input: HumanInput): Promise<void>;

  /** Worker entry point. Long-lived; processes wake-ups. Safe to run N replicas. */
  runWorker(signal: AbortSignal): Promise<void>;

  /**
   * Module completion callback (webhook) ingestion. Accepts the raw body; the owning adapter
   * parses it. Unknown/duplicate callbacks are no-ops. Polling adapters never need this.
   */
  ingestModuleCallback(moduleId: string, rawBody: unknown): Promise<void>;
}

export interface InvestigationView {
  id: InvestigationId;
  status: InvestigationStatus;
  question: string;
  resolvedFocus: string[];                  // human-readable: "Cobalt (HS 8105) - 14 nodes, 9 estimated"
  waitingOn: Array<PendingApproval | PendingClarification>;
  runs: ModuleRunSummary[];                 // incl. reused runs, marked as such
  findings: Finding[];                      // available while still running
  spend: { costUsdCommitted: number; costUsdReused: number; budgetLeft: Budget };
  report?: Report;                          // present once status = "reported"
  timeline: Array<{ at: string; line: string }>; // plain-English audit trail from events
}

export type { ModuleAdapter } from "./modules";
export type { OpenRequest, HumanInput } from "./domain";
