export const GET_LIVE_MISSIONS = `
  subscription GetLiveMissions {
    core_overview(order_by: {updated_at: desc}, limit: 5) {
      id
      status
      core_target {
        name
      }
      core_steps(order_by: {created_at: desc}, limit: 10) {
        id
        status
        core_stepnote {
          content
        }
        core_attackvectors {
          name
        }
      }
    }
  }
`;

/**
 * ExecutionMonitor 專用 Subscription
 * 用途：顯示所有 Overview 及其完整 Step 樹狀圖，支援篩選和搜尋
 */
export const GET_ALL_EXECUTION_STEPS = `
  subscription GetAllExecutionSteps {
    core_overview(order_by: {updated_at: desc}) {
      id
      status
      risk_score
      summary
      plan
      knowledge
      created_at
      updated_at
      core_target {
        id
        name
        description
      }
      core_steps(order_by: {created_at: asc}) {
        id
        status
        created_at
        completed_at
        core_stepnote {
          id
          content
          ai_thoughts
          created_at
        }
        core_attackvectors {
          id
          name
          description
          vector_type
          created_at
        }
      }
    }
  }
`;

export const GET_SKILLS = `
  query GetSkills($search: String) {
    core_skill_template(
      order_by: { usage_count: desc, updated_at: desc }
      where: {
        _or: [
          { name: { _ilike: $search } }
          { description: { _ilike: $search } }
          { tags: { _cast: { String: { _ilike: $search } } } }
        ]
      }
    ) {
      id
      name
      description
      language
      tags
      usage_count
      created_at
      updated_at
      instructions
      script_content
    }
    core_skill_template_aggregate(
      where: {
        _or: [
          { name: { _ilike: $search } }
          { description: { _ilike: $search } }
          { tags: { _cast: { String: { _ilike: $search } } } }
        ]
      }
    ) {
      aggregate {
        count
      }
    }
  }
`;
