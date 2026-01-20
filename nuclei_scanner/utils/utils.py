def map_tech_to_nuclei_tags(tech_name: str) -> List[str]:
    """
    將 Wappalyzer/Httpx 的技術名稱翻譯成 Nuclei 認得的 Tags。
    """
    name_lower = tech_name.lower()
    tags = set()

    # --- 1. 精確/關鍵字對照表 (左邊是特徵，右邊是 Nuclei Tag) ---
    # 這是最核心的部分，根據經驗持續擴充
    keyword_map = {
        # 語言 & 框架
        "php": "php",
        "java": "java",
        "python": "python",
        "django": "django",
        "flask": "flask",
        "spring": "springboot",  # Spring Boot 通常對應 springboot tag
        "laravel": "laravel",
        "ruby": "ruby",
        "rails": "rails",
        "asp.net": "aspnet",
        "node.js": "nodejs",
        "express": "express",
        "go": "go",
        # CMS (重災區)
        "wordpress": "wordpress",
        "drupal": "drupal",
        "joomla": "joomla",
        "magento": "magento",
        "jira": "jira",
        "confluence": "confluence",
        "gitlab": "gitlab",
        "jenkins": "jenkins",
        "grafana": "grafana",
        "kibana": "kibana",
        # Web Servers / Proxies
        "apache": "apache",
        "nginx": "nginx",
        "iis": "iis",  # 關鍵！Wappalyzer 叫 Microsoft IIS
        "tomcat": "tomcat",
        "weblogic": "weblogic",
        "jboss": "jboss",
        "jetty": "jetty",
        # 資料庫 / 其他
        "mysql": "mysql",
        "postgresql": "postgres",
        "redis": "redis",
        "mongodb": "mongodb",
        "elasticsearch": "elasticsearch",
        "docker": "docker",
        "kubernetes": "kubernetes",
        "swagger": "swagger",  # 這個掃 API 很有用
        "graphql": "graphql",
    }

    # --- 2. 匹配邏輯 ---

    # 策略 A: 直接看對照表裡的 key 有沒有出現在技術名稱裡
    # 例如: "Apache Tomcat" 包含 "apache" 和 "tomcat" -> tags: apache, tomcat
    for keyword, tag in keyword_map.items():
        if keyword in name_lower:
            tags.add(tag)

    # 策略 B: 如果什麼都沒對到，嘗試使用原名 (去空白轉小寫) 當作 Tag
    # 這是賭一把，有些冷門技術 Nuclei 剛好也有
    if not tags:
        cleaned_name = name_lower.replace(" ", "")
        # 過濾掉太短或沒意義的
        if len(cleaned_name) > 3:
            tags.add(cleaned_name)

    return list(tags)
