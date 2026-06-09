/**
 * AI Agent Tree Subscription
 *
 * Execution details are no longer read from Hasura core_steps/core_steplog.
 * The UI loads ExecutionGraph/ExecutionNode/ExecutionEvent through Django REST + SSE.
 */
export const GET_AGENT_TREE_SUBSCRIPTION = `
  subscription GetAgentTree($rootThreadId: bigint!, $childPattern: String!) {
    ai_assistant_thread_by_pk(id: $rootThreadId) {
      id
      name
      assistant_id
      is_hidden
      bound_target_id
      created_at
      core_overviews {
        id
        status
        risk_score
        thread_id
        parent_thread_id
        core_target { name }
        aiAssistantThreadByThreadId {
          id
          name
          assistant_id
          is_hidden
          bound_target_id
          created_at
          core_overviews {
            id
            status
            risk_score
            thread_id
            parent_thread_id
            core_target { name }
            aiAssistantThreadByThreadId {
              id
              name
              assistant_id
              is_hidden
              bound_target_id
              created_at
            }
          }
        }
      }
    }
    directChildren: ai_assistant_thread(where: { name: { _ilike: $childPattern } }) {
      id
      name
      assistant_id
      is_hidden
      bound_target_id
      created_at
      coreOverviewsByThreadId(limit: 1, order_by: { id: desc }) {
        id
        status
        risk_score
        parent_thread_id
        core_target { name }
      }
      core_overviews {
        id
        status
        risk_score
        thread_id
        parent_thread_id
        core_target { name }
        aiAssistantThreadByThreadId {
          id
          name
          assistant_id
          is_hidden
          bound_target_id
          created_at
        }
      }
    }
    childOverviews: core_overview(
      where: { parent_thread_id: { _eq: $rootThreadId } }
      order_by: { id: desc }
    ) {
      id
      status
      risk_score
      thread_id
      parent_thread_id
      core_target { name }
      aiAssistantThreadByThreadId {
        id
        name
        assistant_id
        is_hidden
        bound_target_id
        created_at
        core_overviews {
          id
          status
          risk_score
          thread_id
          parent_thread_id
          core_target { name }
          aiAssistantThreadByThreadId {
            id
            name
            assistant_id
            is_hidden
            bound_target_id
            created_at
          }
        }
      }
    }
  }
`;

export const GET_SINGLE_OVERVIEW = `
  query GetSingleOverview($id: bigint!) {
    core_overview_by_pk(id: $id) {
      id
      status
      risk_score
      summary
      business_impact
      plan
      knowledge
      techs
      created_at
      updated_at
      thread_id
      parent_thread_id
      core_target {
        id
        name
        description
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
      version
      is_robust
      is_deprecated
      merged_from
      created_at
      updated_at
      instructions
      script_body
      script_content
      input_schema
      output_schema
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
      aggregate { count }
    }
  }
`;
