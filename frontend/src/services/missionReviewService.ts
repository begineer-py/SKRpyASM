import {
  GetMissionReviewsByOverviewDocument,
  GetMissionReviewDocument,
  GetMissionReviewsDocument,
} from '../gql/graphql';
import type {
  GetMissionReviewsByOverviewQuery,
  GetMissionReviewQuery,
  GetMissionReviewsQuery,
} from '../gql/graphql';
import { executeGraphQL } from './gqlClient';

export type MissionVerdict = 'PENDING' | 'APPROVED' | 'REJECTED' | 'INCONCLUSIVE';

export interface MissionReview {
  id: number;
  overview_id: number;
  verdict: MissionVerdict;
  confidence_score: number;
  reasoning: string;
  rejection_reasons: string[];
  suggested_actions: string[];
  needs_human_review: boolean;
  vuln_count: number;
  confirmed_vuln_count: number;
  high_severity_count: number;
  has_poc_evidence: boolean;
  scan_coverage_pct: number;
  triggered_by: string;
  triggered_by_agent: string;
  reviewed_at?: string | null;
  created_at: string;
}

function toReview(
  r: GetMissionReviewsByOverviewQuery['mission_review'][number],
): MissionReview {
  return {
    id: r.id,
    overview_id: r.overview_id,
    verdict: r.verdict as MissionVerdict,
    confidence_score: r.confidence_score,
    reasoning: r.reasoning,
    rejection_reasons: r.rejection_reasons,
    suggested_actions: r.suggested_actions,
    needs_human_review: r.needs_human_review,
    vuln_count: r.vuln_count,
    confirmed_vuln_count: r.confirmed_vuln_count,
    high_severity_count: r.high_severity_count,
    has_poc_evidence: r.has_poc_evidence,
    scan_coverage_pct: r.scan_coverage_pct,
    triggered_by: r.triggered_by,
    triggered_by_agent: r.triggered_by_agent,
    reviewed_at: r.reviewed_at,
    created_at: r.created_at,
  };
}

export const MissionReviewService = {
  listByOverview: async (overviewId: number): Promise<MissionReview[]> => {
    const data = await executeGraphQL<
      GetMissionReviewsByOverviewQuery,
      { overviewId: number }
    >(GetMissionReviewsByOverviewDocument, { overviewId });
    return (data.mission_review ?? []).map(toReview);
  },

  get: async (reviewId: number): Promise<MissionReview> => {
    const data = await executeGraphQL<GetMissionReviewQuery, { id: number }>(
      GetMissionReviewDocument,
      { id: reviewId },
    );
    return toReview(data.mission_review_by_pk!);
  },

  list: async (params?: {
    needs_human_review?: boolean;
    verdict?: MissionVerdict;
    limit?: number;
  }): Promise<MissionReview[]> => {
    const where: Record<string, unknown> = {};
    if (params?.needs_human_review !== undefined) {
      where.needs_human_review = { _eq: params.needs_human_review };
    }
    if (params?.verdict) {
      where.verdict = { _eq: params.verdict };
    }
    const data = await executeGraphQL<
      GetMissionReviewsQuery,
      { where?: Record<string, unknown>; limit?: number }
    >(GetMissionReviewsDocument, {
      where: Object.keys(where).length > 0 ? where : undefined,
      limit: params?.limit,
    });
    return (data.mission_review ?? []).map(toReview);
  },
};
