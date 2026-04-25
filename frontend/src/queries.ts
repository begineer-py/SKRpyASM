export const GET_LIVE_MISSIONS = `
  subscription GetLiveMissions {
    core_overview(order_by: {updated_at: desc}, limit: 5) {
      id
      status
      risk_score
      core_target {
        name
      }
      core_steps(order_by: {created_at: asc}) {
        id
        status
        core_stepnote {
          content
          ai_thoughts
        }
        core_attackvectors {
          name
          description
        }
      }
    }
  }
`;
