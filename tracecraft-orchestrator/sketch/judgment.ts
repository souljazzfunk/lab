/**
 * The only two places an LLM (Claude via the Anthropic API) is used. Both are single,
 * stateless calls with structured output (tool-use with a JSON schema). There is no
 * long-running agent loop: the "loop" is decide() being re-run on each wake-up, and each
 * call's output is persisted as an event, so replays never re-query the model.
 *
 * Deterministic code does: scope resolution, atomization, dedup, cost gating, confidence,
 * numbers in the report. The LLM does: which modules, over what scope expressions, why,
 * whether we're done, and how to phrase findings for each audience.
 */
import type { Budget, Claim, Finding, FindingId, ModuleId, PlanProposal, PlannerTrace, Report } from "./domain";
import type { ModuleAdapter } from "./modules";

export interface JudgmentConfig {
  planModel: string;        // e.g. a Claude Opus-class model id: plan quality is worth the tokens
  reportModel: string;
  maxFindingsInDigest: number;
}

/** What the planner sees. Built deterministically from state; bounded in size. */
export interface PlanningDigest {
  question: string;
  followUps: string[];
  clarificationAnswers: string[];
  wave: number;
  budgetLeft: Budget;
  modules: Array<{ id: ModuleId } & ModuleAdapter<any, any>["card"]>;
  graphOutline: string;              // products -> key materials -> countries, tier counts, estimated share
  findings: Array<Pick<Finding, "id" | "dimension" | "severity" | "confidence" | "summary" | "leads"> & { subjects: string[] }>;
  alreadyCovered: string[];          // "regulatory-intel over cobalt/CD (reused)" - discourages repeats
  rejectedLastWave: string[];        // why prior steps were rejected, so it can correct itself
}

/**
 * Validation at the boundary (per boundary-discipline): unknown module ids, malformed
 * ScopeExpr, or >N steps become `rejects`, not exceptions. Steps are then resolved and
 * atomized by the runtime; empty/ambiguous scopes become rejects or a clarification.
 */
export function proposePlan(cfg: JudgmentConfig, digest: PlanningDigest): Promise<
  { proposal: PlanProposal; trace: PlannerTrace; rejects: Array<{ step: number; reason: string }> }
> {
  // TODO: system prompt = role + module cards + ScopeExpr grammar + "prefer narrow scopes;
  //       prefer reuse; follow leads only when severity >= medium; say done when the question is answered"
  //       tool schema = PlanProposal; retry once on schema failure with the validation error appended
  //       deterministic checks: module id in registry; card.acceptsNodeKinds vs resolved node kinds
  throw new Error("not implemented");
}

/**
 * The report writer receives findings (with ids and metric names) and returns Claims whose
 * prose uses {{placeholders}}. Validation:
 *  - every cite and figure references a FindingId in `findings`   (else drop claim, log)
 *  - every figure's metric exists on that finding                 (else drop claim, log)
 *  - prose contains no digits outside placeholders (regex)        (else drop claim, log)
 *  - Claim.confidence is recomputed = min(cited finding confidence)
 * Rendering substitutes metric values with units from the adapter; the LLM never types a number.
 */
export function writeReport(
  cfg: JudgmentConfig,
  question: string,
  findings: Finding[],
  gaps: string[],
): Promise<Omit<Report, "generatedFromEventSeq">> {
  throw new Error("not implemented");
}

/** Pure; exported for tests. */
export function validateClaims(claims: Claim[], findings: ReadonlyMap<FindingId, Finding>): { kept: Claim[]; dropped: string[] } {
  throw new Error("not implemented");
}
