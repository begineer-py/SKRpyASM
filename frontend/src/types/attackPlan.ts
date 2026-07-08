/**
 * Attack Plan model types for the new REST API (P3 refactor).
 *
 * Replaces the old schema_version=1 JSONField types with database-backed
 * AttackPlan → Action → AttackVector + AssetVectorLink models.
 *
 * API endpoints live under /api/core/attack-plans, /api/core/actions,
 * /api/core/attack-vectors.
 */

// ─── Vector Types ───────────────────────────────────────────────────────────

export type VectorType =
  | 'WEB_VULN'
  | 'NETWORK_EXPOSURE'
  | 'AUTH_BYPASS'
  | 'INFO_LEAK'
  | 'CONFIG_ISSUE'
  | 'OTHER';

export type VectorStatus =
  | 'IDENTIFIED'
  | 'TESTING'
  | 'EXPLOITABLE'
  | 'EXHAUSTED'
  | 'MITIGATED';

export type AssetType = 'IP' | 'SUBDOMAIN' | 'URL' | 'ENDPOINT' | 'PORT';

export type AssetLinkStatus = 'TARGETED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';

// ─── Action Types ───────────────────────────────────────────────────────────

export type ActionStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'SKIPPED';

// ─── Plan Types ─────────────────────────────────────────────────────────────

export type PlanStatus = 'DRAFT' | 'ACTIVE' | 'COMPLETED' | 'ABANDONED';

// ─── Response Interfaces ────────────────────────────────────────────────────

/** AttackVector — a specific attack surface entry identified during analysis. */
export interface AttackVectorOut {
  id: number;
  overview_id: number;
  name: string;
  description: string | null;
  vector_type: VectorType;
  status: VectorStatus;
  risk_score: number;
  evidence: string | null;
  created_at: string;
  updated_at: string;
}

/** AssetVectorLink — links an attack vector to a concrete asset (IP, subdomain, etc.). */
export interface AssetVectorLinkOut {
  id: number;
  attack_vector_id: number;
  asset_type: AssetType;
  ip_asset_id: number | null;
  subdomain_asset_id: number | null;
  url_asset_id: number | null;
  endpoint_asset_id: number | null;
  port_asset_id: number | null;
  status: AssetLinkStatus;
  agent_thread_id: number | null;
  agent_role: string | null;
  last_result: string | null;
  created_at: string;
  updated_at: string;
}

/** ActionVector — through model linking an Action to an AttackVector. */
export interface ActionVectorOut {
  id: number;
  action_id: number;
  attack_vector_id: number;
  execution_detail: Record<string, unknown> | null;
}

/** Action — a discrete step within an AttackPlan. */
export interface ActionOut {
  id: number;
  target_id: number;
  plan_id: number | null;
  purpose: Record<string, unknown>;
  purpose_text: string | null;
  status: ActionStatus;
  agent_thread_id: number | null;
  agent_role: string | null;
  execution_graph_id: number | null;
  result_summary: string | null;
  order: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  asset_links: AssetVectorLinkOut[];
  attack_vectors: AttackVectorOut[];
  action_vectors: ActionVectorOut[];
}

/** AttackPlan — top-level plan container for a target's attack strategy. */
export interface AttackPlanOut {
  id: number;
  target_id: number;
  thread_id: number | null;
  objective: string;
  scope: Record<string, unknown>;
  status: PlanStatus;
  parent_plan_id: number | null;
  created_at: string;
  updated_at: string;
  actions: ActionOut[]; // only populated in detail view; empty array in list view
}

// ─── API Response Wrappers ──────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// ─── Type Guard ─────────────────────────────────────────────────────────────

/**
 * Type guard: checks if an unknown value conforms to the AttackPlanOut shape.
 *
 * Does structural checking of top-level required fields only.
 * Does NOT validate nested action/vector shapes.
 */
export function isAttackPlanOut(obj: unknown): obj is AttackPlanOut {
  if (typeof obj !== 'object' || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.id === 'number' &&
    typeof o.target_id === 'number' &&
    typeof o.objective === 'string' &&
    typeof o.status === 'string' &&
    Array.isArray(o.actions)
  );
}
