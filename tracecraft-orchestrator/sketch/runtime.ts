/**
 * Thin imperative shell. Owns I/O: the event store, the wake queue, the ledger, adapters,
 * the LLM. Holds no business rules; every "should we?" is answered by investigation.decide().
 *
 * Two kinds of wake-up. A LAUNCH wake (`poll`) belongs to no investigation: adapter.poll ->
 * settleLaunch, else re-enqueue with backoff. It is enqueued once when a launch is claimed.
 *
 * One wake-up of one investigation:
 *   1. acquire lease on stream (short TTL; a second worker gets "busy" and drops the wake)
 *   2. load events -> fold -> state
 *   2b. reconcile: ledger.lookup(state.awaiting) -> append atoms_settled for atoms now done/failed.
 *       (Merge at the read boundary: the ledger is written only by settlers, the stream only by
 *        this worker and by send(). No process ever writes another investigation's stream.)
 *   3. effects = decide(state, now)
 *   4. for each effect: execute(effect) -> events; append(events, expectedSeq)
 *        conflict on append => re-fold and go to 3 (someone else appended, e.g. send())
 *   5. release lease
 * A crash between an external side effect and its append re-runs the same effect key:
 * adapters dedupe on launchId, the ledger on atom key, notify is at-least-once by design.
 */
import type { Effect, InvestigationState } from "./investigation";
import type { InvestigationEvent, InvestigationId, LaunchId, ModuleId } from "./domain";
import type { ModuleAdapter, RunLedger } from "./modules";

/**
 * Writers per stream: the owning worker (under lease, expectedSeq) and send() (human_input only,
 * appended unconditionally - it is an independent fact; evolve dedupes on inputId). send() then
 * enqueues a wake. Nothing else writes a stream.
 */
export interface EventStore {
  load(id: InvestigationId): Promise<{ events: InvestigationEvent[]; seq: number }>;
  /** Fails with Conflict if current seq != expectedSeq. */
  append(id: InvestigationId, expectedSeq: number, events: InvestigationEvent[]): Promise<number>;
  /** Idempotency index for open(requestId) and send(inputId). */
  findByRequestId(requestId: string): Promise<InvestigationId | undefined>;
  lease(id: InvestigationId, ttlMs: number): Promise<{ release(): Promise<void> } | "busy">;
  ledger: RunLedger;                      // same database, separate tables
}

export interface WakeQueue {
  enqueue(msg: Wake, notBefore?: Date): Promise<void>;
  consume(handler: (msg: Wake) => Promise<void>, signal: AbortSignal): Promise<void>;
}
export type Wake =
  | { kind: "investigation"; id: InvestigationId }
  | { kind: "poll"; module: ModuleId; launchId: LaunchId };

export interface GraphSource {
  latestVersion(companyId: string): Promise<string>;
  /** Raw export of the multi-tier analysis. Parsed into GraphSnapshot in scope.ts, nowhere else. */
  fetch(companyId: string, version: string): Promise<unknown>;
}

/** Process one investigation wake-up (steps 1-5 above). */
export async function step(id: InvestigationId): Promise<void> { throw new Error("not implemented"); }

/** Process one launch wake-up: poll the owning adapter once; settle or re-enqueue with backoff. */
export async function pollLaunch(module: ModuleId, launchId: LaunchId): Promise<void> { throw new Error("not implemented"); }

/**
 * Effect execution. Each branch returns the events it produced; none mutates state.
 *  plan:       digest(state) -> judgment.proposePlan
 *              -> per step: scope.resolve (pinned graph version = the one at `opened`, unless a
 *                 follow-up explicitly asks for the latest), adapter.project, atomKey,
 *                 ledger.lookup -> split atoms into reused / to-run
 *              -> card.acceptsNodeKinds check; adapter.estimate(to-run atoms); gate(sum) per wave
 *              -> events: plan_proposed, launch_planned*, plan_rejected_steps, clarification_needed?
 *              (steps whose atoms are ALL reused produce a launch_planned with atoms=[], no cost)
 *  start:      ledger.claim(launchId, atoms); adapter.launch(owned atoms); enqueue launch wake
 *              (polling adapters); ledger.subscribe on this and every foreign in-flight launch
 *              -> launch_started
 *  release:    ledger.unsubscribe; if 0 subscribers left: adapter.cancel?(launchId)
 *  notify:     outbound channel (email/Slack) - outside this sketch
 *  synthesize: judgment.writeReport(findings, gaps) -> report_written
 */
export async function execute(effect: Effect, s: InvestigationState): Promise<InvestigationEvent[]> {
  throw new Error("not implemented");
}

/**
 * Shared by poll and webhook paths. adapter.toFindings -> assign FindingId/Provenance/confidence
 * -> ledger.settle (idempotent, conditional on state=running) -> enqueue a wake for each
 * subscriber. It does NOT touch investigation streams; each investigation picks the result up
 * in its own step 2b. A lost wake is harmless: the poll backstop wakes the investigation later.
 */
export async function settleLaunch(adapter: ModuleAdapter<any, any>, launchId: LaunchId, output: unknown): Promise<void> {
  throw new Error("not implemented");
}
