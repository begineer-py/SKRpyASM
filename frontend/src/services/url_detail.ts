// src/services/url_detail.ts
// GraphQL query + types for the URL Detail Page

export const GET_URL_DETAIL_QUERY = `
  query GetURLDetail($url_id: bigint!) {
    core_urlresult_by_pk(id: $url_id) {
      id
      url
      final_url
      status_code
      title
      method
      content_length
      content_fetch_status
      is_external_redirect
      is_important
      is_tech_analyzed
      discovery_source
      used_flaresolverr
      created_at

      # 所屬子域名 (M2M through core_urlresult_related_subdomains)
      core_urlresult_related_subdomains {
        core_subdomain {
          id
          name
        }
      }

      # 技術棧
      core_techstacks {
        id
        name
        version
        categories
      }

      # 漏洞掃描
      core_nucleiscans(order_by: {created_at: desc}, limit: 5) {
        id
        status
        created_at
        completed_at
      }

      # 漏洞
      core_vulnerabilities(order_by: {severity: asc}, limit: 20) {
        id
        severity
        name
        description
        template_id
      }

      # AI 分析
      core_urlaianalyses(limit: 1, order_by: {created_at: desc}) {
        id
        status
        summary
        inferred_purpose
        potential_vulnerabilities
        recommended_actions
        command_actions
        created_at
        completed_at
        error_message
      }

      # HTTP Headers
      headers

      # Meta 標籤 (只有 attributes JSONField)
      core_metatags(limit: 20) {
        id
        attributes
      }

      # Links (no is_external field)
      core_links(limit: 30) {
        id
        href
        text
      }

      # Forms (uses parameters not inputs_json)
      core_forms(limit: 10) {
        id
        action
        method
        parameters
      }
    }
  }
`;
