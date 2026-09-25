/**
 * Scope: turning "cobalt" / "Supplier X" / "DRC" / "the refiners behind finding F" into a
 * concrete, versioned node set. Deterministic. The LLM never produces node ids directly; it
 * produces a ScopeExpr, and this file decides what that means against the graph.
 */
import type { Focus, FindingId, NodeId, NodeRef, ResolvedScope, ResolvedScopeSnapshot, Finding, ScopeExpr } from "./domain";
import type { GraphSource } from "./runtime";

export type { ScopeExpr };

export type Resolution =
  | { ok: true; scope: ResolvedScope }
  | { ok: false; kind: "ambiguous"; term: string; candidates: Array<{ node: NodeRef; matchScore: number }> } // -> clarification
  | { ok: false; kind: "empty"; explanation: string };                      // -> rejected plan step

/**
 * Resolve against one pinned graph version.
 * Invariants:
 *  - Output nodes all exist in `graphVersion`.
 *  - Inclusion confidence of a node = max over paths (product of edge/existence confidences).
 *    Estimated tiers therefore stay in scope but carry their uncertainty forward to Findings.
 *  - Pure given (expr, graph snapshot, prior findings). Same inputs -> byte-identical snapshot,
 *    which is what makes launch dedup work.
 */
export function resolve(
  expr: ScopeExpr,
  graph: GraphSnapshot,
  priorFindings: ReadonlyMap<FindingId, Finding>,
): Resolution {
  // TODO:
  //  material  -> graph.aliasIndex (names, synonyms, HS prefixes) -> raw_material nodes
  //               then include every node on a path from company to that material (suppliers/sites carrying it)
  //  supplier  -> exact id | alias exact | fuzzy (>1 hit above threshold => ambiguous)
  //  region    -> ISO lookup, else sub-national gazetteer -> sites whose geo falls in it
  //  fromFindings -> union of subjects (unknown id => empty w/ explanation)
  //  expand    -> BFS along supply edges `tiers` steps, multiply confidences
  //  intersect/union -> set ops; confidence = min / max
  throw new Error("not implemented");
}

/** Focus (from UI or LLM mention extraction) -> ScopeExpr. Union within a field, intersect across fields. */
export function focusToExpr(focus: Focus): ScopeExpr {
  throw new Error("not implemented");
}

export function snapshot(s: ResolvedScope): ResolvedScopeSnapshot { throw new Error("not implemented"); }
export function rehydrate(s: ResolvedScopeSnapshot): ResolvedScope { throw new Error("not implemented"); }

/** In-memory, immutable view of one graph version with the indexes resolve() needs. */
export interface GraphSnapshot {
  version: string;
  node(id: NodeId): NodeRef | undefined;
  upstream(id: NodeId): Array<{ to: NodeId; confidence: number }>;
  downstream(id: NodeId): Array<{ to: NodeId; confidence: number }>;
  aliasIndex: { lookup(term: string, kind?: NodeRef["kind"]): Array<{ node: NodeRef; score: number }> };
}
export function loadSnapshot(src: GraphSource, companyId: string, version: string): Promise<GraphSnapshot> {
  throw new Error("not implemented");
}
