export const GET_LIVE_MISSIONS = `
  subscription GetLiveMissions {
    core_overview(order_by: {updated_at: desc}, limit: 10) {
      id
      status
      thread_id
      parent_thread_id
      core_target {
        id
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
 * Chat 區域實時 Step 更新 Subscription
 * 用途：在 Chat 窗口中實時顯示最近的 Step 執行進度
 * 訂閱最近 5 個 Overview 及其最新 Step，頻繁更新
 */
export const GET_RECENT_STEPS_UPDATES = `
  subscription GetRecentStepsUpdates {
    core_overview(order_by: {updated_at: desc}, limit: 10) {
      id
      status
      updated_at
      thread_id
      parent_thread_id
      core_target {
        id
        name
      }
      core_steps(order_by: {created_at: desc}, limit: 20) {
        id
        status
        created_at
        completed_at
        core_stepnote {
          content
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
      thread_id
      parent_thread_id
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

/**
 * AI Agent Tree Subscription
 * 根 thread (hacker_assistant_agent) 以及所有它召喚的 automation_agent sub-threads，
 * 包含每個 sub-thread 關聯的 Overview 狀態/風險/目標。
 * 使用兩個來源取聯集：
 *   1. core_overview.parent_thread_id = rootThreadId  → aiAssistantThreadByThreadId
 *   2. ai_assistant_thread.name = 命名慣例
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
        core_steps(order_by: { id: desc }, limit: 20) {
          id
          status
          operation_type
          created_at
          completed_at
        }
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
            core_steps(order_by: { id: desc }, limit: 20) {
              id
              status
              operation_type
              created_at
              completed_at
            }
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
        core_steps(order_by: { id: desc }, limit: 20) {
          id
          status
          operation_type
          created_at
          completed_at
        }
      }
      core_overviews {
        id
        status
        risk_score
        thread_id
        parent_thread_id
        core_target { name }
        core_steps(order_by: { id: desc }, limit: 20) {
          id
          status
          operation_type
          created_at
          completed_at
        }
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
      core_steps(order_by: { id: desc }, limit: 20) {
        id
        status
        operation_type
        created_at
        completed_at
      }
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
          core_steps(order_by: { id: desc }, limit: 20) {
            id
            status
            operation_type
            created_at
            completed_at
          }
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

/**
 * Script Executions for a specific Step
 * 用途：在 ExecutionMonitorPage 顯示某個 Step 執行過的所有腳本
 */
export const GET_SCRIPT_EXECUTIONS = `
  query GetScriptExecutions($stepId: bigint!) {
    core_script_execution(
      where: { step_id: { _eq: $stepId } }
      order_by: { started_at: desc }
    ) {
      id
      status
      validation_status
      script_language
      args_string
      input_json
      output_json
      raw_output
      exit_code
      error_message
      validation_error
      execution_duration_ms
      started_at
      completed_at
      skill {
        id
        name
        version
        is_robust
      }
      attack_vector {
        id
        name
      }
    }
  }
`;

/**
 * Target-level Step Monitoring (Version 3)
 * 用途：從 Target 級別查詢所有相關的 Steps
 * 策略：先查 Overview，再獲取關聯的 Steps（不包含日誌，日誌通過 SSE 實時獲取）
 */
export const GET_TARGET_ACTIVE_STEPS = `
  query GetTargetActiveSteps($targetId: bigint!) {
    core_overview(
      where: { target_id: { _eq: $targetId } }
      order_by: { updated_at: desc }
    ) {
      id
      status
      summary
      risk_score
      created_at
      updated_at
      core_steps(order_by: { created_at: desc }) {
        id
        status
        operation_type
        created_at
        completed_at
        core_stepnote {
          content
          ai_thoughts
        }
        script_executions(order_by: { started_at: desc }, limit: 5) {
          id
          status
          validation_status
          script_language
          started_at
        }
      }
    }
    core_step(
      where: { overview_id: { _is_null: true } }
      order_by: { created_at: desc }
      limit: 50
    ) {
      id
      status
      operation_type
      created_at
      completed_at
      core_stepnote {
        content
        ai_thoughts
      }
      script_executions(order_by: { started_at: desc }, limit: 5) {
        id
        status
        validation_status
        script_language
        started_at
      }
    }
  }
`;

/**
 * Target Overview Monitoring (實時訂閱)
 * 用途：顯示 Target 的 Steps 摘要，持續監控
 * 注意：日誌通過 useStepLogStream (SSE) 單獨實時推送，不在此查詢中
 */
export const SUBSCRIBE_TARGET_STEPS = `
  subscription SubscribeTargetSteps($targetId: bigint!) {
    core_overview(
      where: { target_id: { _eq: $targetId } }
      order_by: { updated_at: desc }
    ) {
      id
      status
      created_at
      updated_at
      core_steps(order_by: { created_at: desc }, limit: 50) {
        id
        status
        operation_type
        created_at
        completed_at
        overview_id
        core_stepnote {
          content
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

/**
 * Step Log Real-time Subscription (via Hasura GQL, replaces SSE)
 * 用途：即時訂閱單一 Step 的所有工具調用日誌，取代 SSE EventSource
 * 需要 Hasura 追蹤 core_steplog 表
 */
export const SUBSCRIBE_STEP_LOGS = `
  subscription SubscribeStepLogs($stepId: bigint!) {
    core_steplog(
      where: { step_id: { _eq: $stepId } }
      order_by: { sequence: asc }
    ) {
      id
      step_id
      sequence
      level
      tag
      message
      action_status
      execution_time_ms
      created_at
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
      aggregate {
        count
      }
    }
  }
`;
