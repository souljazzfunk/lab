/**
 * The brain, minus the LLM: a PURE decider over one investigation's event log.
 *
 *   state   = events.reduce(evolve, initial)
 *   effects = decide(state, now)
 *
 * The runtime executes effects and appends the resulting events. Because decide() is pure
 * and every effect carries a deterministic id, a crash anywhere just means "fold again and
 * re-issue the same effects", which are all idempotent (per make-operations-idempotent).
 * No timers, no in-memory agent loop survives between wake-ups: the log is the agent's memory.
 */
import type {
  ApprovalId, AtomKey, Budget, Finding, FindingId, InvestigationEvent, InvestigationId,
  InvestigationStatus, LaunchId, PlannedLaunch, PendingApproval, PendingClarification, RunEstimate,
} from "./domain";

export interface InvestigationState {
  id: InvestigationId;
  seq: number;                                   // last applied event seq
  question: string;
  followUps: string[];                           // appended by follow_up inputs; each reopens planning
  budget: Budget;
  wave: number;                                  // current plan round (0-based)
  planned: Map<LaunchId, PlannedLaunch>;
  decisions: Map<ApprovalId, "approved" | "declined">;
  started: Set<LaunchId>;
  /** Atoms this investigation is waiting on, from ANY launch. Wave is settled when empty. */
  awaiting: Set<AtomKey>;
  findings: Map<FindingId, Finding>;
  failedAtoms: Set<AtomKey>;
  plannerSaysDone: boolean;                      // last proposal set done=true
  waveHasProposal: boolean;
  openClarification?: PendingClarification;
  gaps: string[];                                // declined waves, rejected steps, budget cuts, failures
  committed: RunEstimate;                        // summed from approved/auto launches, never incremented ad hoc
  status: InvestigationStatus;                   // derived in evolve, never set by the runtime
  reportSeq?: number;
}

export function initial(id: InvestigationId): InvestigationState { throw new Error("not implemented"); }

/** Pure, total. Unknown/duplicate events (same inputId, same launchId settle) are no-ops. */
export function evolve(s: InvestigationState, e: InvestigationEvent): InvestigationState {
  // TODO per event:
  //  opened            -> question, budget, status=planning
  //  plan_proposed     -> waveHasProposal=true, plannerSaysDone=proposal.done
  //  launch_planned    -> planned.set; if gate=auto add atoms to awaiting + committed;
  //                       reused findings go straight into `findings`
  //  human_input       -> approve: decisions.set, move that wave's launches' atoms into awaiting
  //                       decline: decisions.set, gaps.push("wave N declined by X")
  //                       clarify: clear openClarification (the answer is fed to the next plan call)
  //                       follow_up: followUps.push, wave++, waveHasProposal=false, plannerSaysDone=false
  //                       cancel: status=cancelled (decide then emits `release` for started launches)
  //  launch_started    -> started.add
  //  atoms_settled     -> findings += , awaiting -= settled ∪ failed, failedAtoms += failed
  //  report_written    -> status=reported, reportSeq
  //  status is recomputed at the end from the fields above (single source of truth)
  throw new Error("not implemented");
}

/** Everything the shell may do. `key` is the idempotency key; re-issuing is always safe. */
export type Effect =
  | { kind: "plan"; key: string; wave: number }                       // call judgment.proposePlan, expand, append
  | { kind: "start"; key: string; launchId: LaunchId }                // ledger.claim + adapter.launch + subscribe
  | { kind: "release"; key: string; launchId: LaunchId }              // ledger.unsubscribe (+ adapter.cancel at 0)
  | { kind: "notify"; key: string; what: PendingApproval | PendingClarification | { kind: "report_ready" } }
  | { kind: "synthesize"; key: string; uptoSeq: number };             // call judgment.writeReport

export function decide(s: InvestigationState, now: Date): Effect[] {
  // TODO (order matters only for readability; all rules are independent):
  //  if status == cancelled: return release(l) for each started, unsettled launch (then [])
  //  if status in {reported, failed}: return []
  //  if openClarification: return [notify(clarification)]
  //  if !waveHasProposal: return [plan(wave)]
  //  for each planned launch in wave not started:
  //      gate=auto or decisions[approvalId(wave)]=approved -> start(launchId)
  //  if some needs_approval launch in wave undecided -> notify(pendingApproval(s))
  //  (no poll effect: polling is per LAUNCH, owned by the runtime's launch wake, not by any
  //   investigation. So a shared launch keeps being polled even if the investigation that
  //   started it is cancelled; settle() wakes every subscriber.)
  //  if awaiting.size == 0 and every launch in wave is started|declined:
  //      if plannerSaysDone || wave+1 >= budget.maxWaves || budgetLeft(s) <= 0 -> synthesize(seq)
  //      else -> plan(wave+1)
  throw new Error("not implemented");
}

/**
 * Cost gate. Pure policy; the LLM never decides whether to spend.
 *  - committed.costUsd + wave.costUsd > maxCostUsd -> "over_budget" (step rejected, recorded as a gap)
 *  - wave.costUsd < autoApprove.belowCostUsd AND wave.hoursP90 < autoApprove.belowHoursP90 -> "auto"
 *  - else "needs_approval"
 */
export function gate(wave: RunEstimate, s: InvestigationState): "auto" | "needs_approval" | "over_budget" {
  throw new Error("not implemented");
}

export function approvalId(id: InvestigationId, wave: number): ApprovalId { throw new Error("not implemented"); }

/** Derivations used by view() - never stored. */
export function pendingApproval(s: InvestigationState): PendingApproval | undefined { throw new Error("not implemented"); }
