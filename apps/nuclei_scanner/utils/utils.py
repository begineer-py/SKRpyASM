from typing import List


def map_tech_to_nuclei_tags(tech_name: str) -> List[str]:
    """
    史詩級加強版：將技術名稱轉換為 Nuclei Tags
    """
    name_lower = tech_name.lower()
    tags = set()

    # --- 1. 大規模技術對照表 ---
    keyword_map = {
        # --- CMS 重災區 ---
        "wordpress": "wordpress",
        "adobe experience manager": "aem,aem-cms,adobe",
        "aem": "aem,aem-cms",
        "drupal": "drupal",
        "joomla": "joomla",
        "magento": "magento",
        "ghost": "ghost",
        "strapi": "strapi",
        "bitrix": "bitrix",
        "sitecore": "sitecore",
        "liferay": "liferay",
        # --- Java & Middleware (針對 Bluehost 的 AEM 架構) ---
        "java": "java,jsp",
        "apache sling": "sling,aem",
        "sling": "sling",
        "jetty": "jetty",
        "tomcat": "tomcat",
        "jboss": "jboss",
        "wildfly": "wildfly",
        "weblogic": "weblogic",
        "websphere": "websphere",
        "spring": "spring,springboot",
        "struts": "struts",
        "hibernate": "hibernate",
        "quartz": "quartz",
        # --- 語言 & 框架 ---
        "php": "php",
        "laravel": "laravel",
        "symfony": "symfony",
        "codeigniter": "codeigniter",
        "yii": "yii",
        "python": "python",
        "django": "django",
        "flask": "flask",
        "fastapi": "fastapi",
        "ruby": "ruby",
        "rails": "rails",
        "node.js": "nodejs",
        "express": "express",
        "asp.net": "aspnet",
        "dotnet": "dotnet",
        "golang": "go",
        # --- Web Servers ---
        "nginx": "nginx",
        "apache http server": "apache",
        "apache": "apache",
        "microsoft iis": "iis",
        "iis": "iis",
        "caddy": "caddy",
        "lighttpd": "lighttpd",
        "openresty": "openresty",
        # --- 資料庫 & 緩存 ---
        "mysql": "mysql",
        "postgresql": "postgres",
        "redis": "redis",
        "mongodb": "mongodb",
        "elasticsearch": "elasticsearch",
        "kibana": "kibana",
        "solr": "solr",
        "memcached": "memcached",
        "rabbitmq": "rabbitmq",
        # --- DevOps & 基礎設施 ---
        "docker": "docker",
        "kubernetes": "k8s,kubernetes",
        "jenkins": "jenkins",
        "gitlab": "gitlab",
        "github": "github",
        "grafana": "grafana",
        "prometheus": "prometheus",
        "portainer": "portainer",
        "consul": "consul",
        "terraform": "terraform",
        # --- 安全 & API ---
        "cloudflare": "cloudflare",
        "modsecurity": "modsecurity",
        "recharge": "recharge",
        "swagger": "swagger,openapi",
        "graphql": "graphql",
        "auth0": "auth0",
        "keycloak": "keycloak",
        "okta": "okta",
        # --- 其他特定組件 ---
        "jquery": "jquery",
        "bootstrap": "bootstrap",
        "font awesome": "fontawesome",
        "google tag manager": "gtm",
        "onetrust": "onetrust",
    }

    # --- 2. 匹配邏輯 ---
    for keyword, tag_str in keyword_map.items():
        if keyword in name_lower:
            # 支援一個 Key 對應多個 Tags (用逗號隔開)
            for t in tag_str.split(","):
                tags.add(t)

    # --- 3. 備用邏輯：嘗試提取技術名稱的第一個單詞作為 Tag ---
    if not tags:
        parts = name_lower.split()
        if parts and len(parts[0]) > 2:
            tags.add(parts[0])

    return list(tags)
