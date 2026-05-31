// src/services/subdomains_detail.ts

// 终极查询，用于获取单个子域名的所有深度情报
export const GET_SUBDOMAIN_DETAIL_QUERY = `
  query GetSubdomainDetail($subdomain_id: bigint!) {
    # 1. 通过主键 (ID) 查询子域名本身及其直接关联的资产
    core_subdomain_by_pk(id: $subdomain_id) {
      # 基础信息
      id
      name
      created_at

      is_active
      is_resolvable
      
      # 安全状态
      is_cdn
      cdn_name
      is_waf
      waf_name
      
      # 关联的 IP 地址 (通过中间表)
      core_subdomain_ips {
        core_ip {
          id
          address
          version
        }
      }

      
      # 关联的 AI 分析结果 (取最新的)
      core_initialaianalyses(limit: 1, order_by: {created_at: desc}) {
        # 核心分析字段
        summary
        inferred_purpose
        risk_score
        worth_deep_analysis
        
        # 元数据
        status
        error_message
        created_at
        completed_at
        raw_response # 调试用
      }
    }

    # 2. 独立查询 URL 结果 (后续需要优化为有关联的查询)
    # 注意: 这里仍然会拉取所有 URL，然后由前端过滤。
    core_urlresult {
      url
      id
      content_length
      content_fetch_status
    }
  }
`;