"""
Enhanced Payload Mapping Configuration for HTTP Sender
基於 SecLists 的詳細參數到字典映射表
"""

SECLISTS_BASE = "/usr/share/wordlists/SecLists"

PAYLOAD_MAPPING = {
    "sqli": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/Generic-SQLi.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/Generic-BlindSQLi.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/SQLi-Polyglots.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/sqli.auth.bypass.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/MySQL.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/MSSQL.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/Oracle.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/NoSQL.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/quick-SQLi.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/SQLi/MySQL-SQLi-Login-Bypass.fuzzdb.txt",
        ],
        "keywords": [
            "id",
            "user",
            "admin",
            "login",
            "search",
            "query",
            "filter",
            "data",
        ],
        "param_types": ["integer", "string"],
    },
    "xss": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/XSS/robot-friendly/XSS-RSNAKE.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/robot-friendly/XSS-Jhaddix.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/robot-friendly/XSS-Cheat-Sheet-PortSwigger.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/robot-friendly/XSS-payloadbox.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/robot-friendly/XSS-BruteLogic.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/robot-friendly/XSS-Fuzzing.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/robot-friendly/XSS-OFJAAAH.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/human-friendly/XSS-RSNAKE.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/human-friendly/XSS-Jhaddix.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/human-friendly/XSS-payloadbox.txt",
            f"{SECLISTS_BASE}/Fuzzing/XSS/Polyglots/XSS-Polyglots.txt",
        ],
        "keywords": [
            "comment",
            "message",
            "content",
            "description",
            "name",
            "title",
            "search",
        ],
        "param_types": ["string", "text"],
    },
    "command_injection": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/command-injection-commix.txt",
            f"{SECLISTS_BASE}/Fuzzing/UnixAttacks.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Windows-Attacks.fuzzdb.txt",
        ],
        "keywords": ["cmd", "command", "exec", "run", "execute", "file", "path"],
        "param_types": ["string"],
    },
    "file_inclusion": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-Jhaddix.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-gracefulsecurity-windows.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-gracefulsecurity-linux.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-linux-and-windows_by-1N3@CrowdShield.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-Windows-adeadfed.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-LFISuite-pathtotest.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-LFISuite-pathtotest-huge.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/LFI-etc-files-of-all-linux-packages.txt",
            f"{SECLISTS_BASE}/Fuzzing/LFI/OMI-Agent-Linux.txt",
        ],
        "keywords": ["file", "path", "dir", "folder", "include", "page", "document"],
        "param_types": ["string"],
    },
    "email": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/email-top-100-domains.txt",
        ],
        "keywords": ["email", "mail", "username", "user"],
        "param_types": ["string"],
    },
    "credentials": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/login_bypass.txt",
        ],
        "keywords": ["password", "pass", "pwd", "login", "user", "username"],
        "param_types": ["string"],
    },
    "api_keys": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/URI-XSS.fuzzdb.txt",
        ],
        "keywords": ["key", "token", "api", "secret", "auth", "bearer"],
        "param_types": ["string"],
    },
    "discovery": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/big-list-of-naughty-strings.txt",
        ],
        "keywords": ["dir", "directory", "folder", "path", "file"],
        "param_types": ["string"],
    },
    "numbers": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/3-digits-000-999.txt",
            f"{SECLISTS_BASE}/Fuzzing/4-digits-0000-9999.txt",
            f"{SECLISTS_BASE}/Fuzzing/5-digits-00000-99999.txt",
            f"{SECLISTS_BASE}/Fuzzing/6-digits-000000-999999.txt",
            f"{SECLISTS_BASE}/Fuzzing/numeric-fields-only.txt",
        ],
        "keywords": ["id", "num", "number", "count", "page", "limit", "offset"],
        "param_types": ["integer", "number"],
    },
    "boolean": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/FormatString-Jhaddix.txt",
        ]
    },
    "structured_data": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/JSON.Fuzzing.txt",
            f"{SECLISTS_BASE}/Fuzzing/XML-FUZZ.txt",
            f"{SECLISTS_BASE}/Fuzzing/XXE-Fuzzing.txt",
        ],
        "keywords": ["json", "xml", "data", "config", "settings"],
        "param_types": ["json", "xml", "object"],
    },
    "ldap": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/LDAP.Fuzzing.txt",
            f"{SECLISTS_BASE}/Fuzzing/LDAP-active-directory-attributes.txt",
            f"{SECLISTS_BASE}/Fuzzing/LDAP-active-directory-classes.txt",
            f"{SECLISTS_BASE}/Fuzzing/LDAP-openldap-attributes.txt",
            f"{SECLISTS_BASE}/Fuzzing/LDAP-openldap-classes.txt",
        ],
        "keywords": ["ldap", "dn", "ou", "search", "filter"],
        "param_types": ["string"],
    },
    "ssrf": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/URI-XSS.fuzzdb.txt",
        ],
        "keywords": ["url", "uri", "link", "redirect", "next", "data", "reference", "site", "html", "val", "validate", "domain", "callback", "return", "page", "feed", "host", "port", "path", "ext", "file", "directory", "base", "class", "url", "do", "func", "fa", "callback", "jsonp", "code", "state", "referrer", "origin"],
        "param_types": ["string"],
    },
    "ssti": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/template-engines-expression.txt",
            f"{SECLISTS_BASE}/Fuzzing/template-engines-special-vars.txt",
        ],
        "keywords": ["template", "render", "view", "page", "body", "content", "msg", "tpl"],
        "param_types": ["string"],
    },
    "xxe": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/XXE-Fuzzing.txt",
        ],
        "keywords": ["xml", "xsd", "xsl", "doc", "feed", "doctype"],
        "param_types": ["string"],
    },
    "ssi": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/SSI-Injection-Jhaddix.txt",
        ],
        "keywords": ["shtml", "shtm", "stm"],
        "param_types": ["string"],
    },
    "upload": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/extensions-Bo0oM.txt",
            f"{SECLISTS_BASE}/Fuzzing/extensions-compressed.fuzz.txt",
            f"{SECLISTS_BASE}/Fuzzing/extensions-most-common.fuzz.txt",
            f"{SECLISTS_BASE}/Fuzzing/extensions-skipfish.fuzz.txt",
            f"{SECLISTS_BASE}/Fuzzing/file-extensions-all-cases.txt",
            f"{SECLISTS_BASE}/Fuzzing/file-extensions-lower-case.txt",
            f"{SECLISTS_BASE}/Fuzzing/file-extensions-upper-case.txt",
            f"{SECLISTS_BASE}/Fuzzing/file-extensions.txt",
        ],
        "keywords": ["file", "upload", "image", "avatar", "document", "attachment", "media"],
        "param_types": ["file"],
    },
    "http_methods": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/http-request-methods.txt",
        ],
        "keywords": ["method", "action", "_method"],
        "param_types": ["string"],
    },
    "special_chars": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/special-chars.txt",
            f"{SECLISTS_BASE}/Fuzzing/special-chars + urlencoded.txt",
            f"{SECLISTS_BASE}/Fuzzing/Metacharacters.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/fuzz-Bo0oM.txt",
            f"{SECLISTS_BASE}/Fuzzing/fuzz-Bo0oM-friendly.txt",
            f"{SECLISTS_BASE}/Fuzzing/FuzzingStrings-SkullSecurity.org.txt",
        ],
        "keywords": ["q", "search", "query", "keyword", "fuzz", "test"],
        "param_types": ["string"],
    },
    "os_fingerprint": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/os-names.txt",
            f"{SECLISTS_BASE}/Fuzzing/os-names-mutated.txt",
        ],
        "keywords": ["os", "system", "platform"],
        "param_types": ["string"],
    },
    "java_classes": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/fully-qualified-java-classes.txt",
        ],
        "keywords": ["class", "classname", "type"],
        "param_types": ["string"],
    },
    "environment": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/environment-identifiers.txt",
        ],
        "keywords": ["env", "environment", "config"],
        "param_types": ["string"],
    },
    "dates": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/Dates/2024/2024-MM-DD.txt",
            f"{SECLISTS_BASE}/Fuzzing/Dates/2023/2023-MM-DD.txt",
            f"{SECLISTS_BASE}/Fuzzing/Dates/2025/2025-MM-DD.txt",
            f"{SECLISTS_BASE}/Fuzzing/Dates/2022/2022-MM-DD.txt",
            f"{SECLISTS_BASE}/Fuzzing/Dates/2021/2021-MM-DD.txt",
            f"{SECLISTS_BASE}/Fuzzing/Dates/2020/2020-MM-DD.txt",
            f"{SECLISTS_BASE}/Fuzzing/Dates/2019/2019-MM-DD.txt",
        ],
        "keywords": ["date", "time", "timestamp", "from", "to", "start", "end"],
        "param_types": ["string", "date"],
    },
    "amounts": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/Amounts/all.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/zero.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/one.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/ten.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/hundred.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/thousand.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/ten_thousand.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/hundred_thousand.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/milion.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/zero_point_one.txt",
            f"{SECLISTS_BASE}/Fuzzing/Amounts/other.txt",
        ],
        "keywords": ["amount", "price", "cost", "total", "sum", "quantity", "qty"],
        "param_types": ["integer", "number", "float"],
    },
    "databases": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/Databases/Postgres-Enumeration.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/OracleDB-SID.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/MSSQL-Enumeration.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/MySQL-Read-Local-Files.fuzzdb.txt",
            f"{SECLISTS_BASE}/Fuzzing/Databases/db2enumeration.fuzzdb.txt",
        ],
        "keywords": ["db", "database", "table", "schema", "query"],
        "param_types": ["string"],
    },
    "user_agents": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/User-Agents/UserAgents.fuzz.txt",
            f"{SECLISTS_BASE}/Fuzzing/User-Agents/user-agents-whatismybrowserdotcom-large.txt",
        ],
        "keywords": ["user-agent", "ua", "browser"],
        "param_types": ["string"],
    },
    "ibmmq": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/IBMMQSeries-channels.txt",
        ],
        "keywords": ["channel", "queue", "ibmmq", "mq"],
        "param_types": ["string"],
    },
    "curl_protocols": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/curl-protocols.txt",
        ],
        "keywords": ["protocol", "scheme"],
        "param_types": ["string"],
    },
    "locale": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/regional_country-codes-lower-case.txt",
            f"{SECLISTS_BASE}/Fuzzing/regional_country-codes-upper-case.txt",
            f"{SECLISTS_BASE}/Fuzzing/regional_country-codes.txt",
            f"{SECLISTS_BASE}/Fuzzing/regional_languages-codes.txt",
            f"{SECLISTS_BASE}/Fuzzing/regional_locale-codes.txt",
        ],
        "keywords": ["locale", "lang", "language", "country", "region", "timezone"],
        "param_types": ["string"],
    },
    "php_magic": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/php-magic-methods.txt",
        ],
        "keywords": ["php", "function", "method", "class"],
        "param_types": ["string"],
    },
    "alphanum": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/alphanum-case-extra.txt",
            f"{SECLISTS_BASE}/Fuzzing/alphanum-case.txt",
            f"{SECLISTS_BASE}/Fuzzing/1-4_all_letters_a-z.txt",
            f"{SECLISTS_BASE}/Fuzzing/char.txt",
        ],
        "keywords": ["code", "token", "key", "char", "letter"],
        "param_types": ["string"],
    },
    "unicode": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/Unicode.txt",
        ],
        "keywords": ["char", "text", "input"],
        "param_types": ["string"],
    },
    "uri_hex": {
        "paths": [
            f"{SECLISTS_BASE}/Fuzzing/URI-hex.txt",
            f"{SECLISTS_BASE}/Fuzzing/doble-uri-hex.txt",
        ],
        "keywords": ["hex", "encoded", "uri"],
        "param_types": ["string"],
    },
}

PAYLOAD_STRUCTURE = {
    "injection_payloads": {
        "sqli": PAYLOAD_MAPPING["sqli"]["paths"],
        "xss": PAYLOAD_MAPPING["xss"]["paths"],
        "command_injection": PAYLOAD_MAPPING["command_injection"]["paths"],
        "file_inclusion": PAYLOAD_MAPPING["file_inclusion"]["paths"],
        "ldap": PAYLOAD_MAPPING["ldap"]["paths"],
        "xxe": PAYLOAD_MAPPING["xxe"]["paths"],
        "ssti": PAYLOAD_MAPPING["ssti"]["paths"],
        "ssrf": PAYLOAD_MAPPING["ssrf"]["paths"],
    },
    "authentication_payloads": {
        "credentials": PAYLOAD_MAPPING["credentials"]["paths"],
        "emails": PAYLOAD_MAPPING["email"]["paths"],
    },
    "discovery_payloads": {
        "directories": PAYLOAD_MAPPING["discovery"]["paths"],
        "files": PAYLOAD_MAPPING["upload"]["paths"],
        "special_chars": PAYLOAD_MAPPING["special_chars"]["paths"],
    },
    "data_type_payloads": {
        "numbers": PAYLOAD_MAPPING["numbers"]["paths"],
        "booleans": PAYLOAD_MAPPING["boolean"]["paths"],
        "strings": PAYLOAD_MAPPING["xss"]["paths"],
        "structured": PAYLOAD_MAPPING["structured_data"]["paths"],
        "dates": PAYLOAD_MAPPING["dates"]["paths"],
        "amounts": PAYLOAD_MAPPING["amounts"]["paths"],
    },
    "fuzzing_payloads": {
        "os_fingerprint": PAYLOAD_MAPPING["os_fingerprint"]["paths"],
        "http_methods": PAYLOAD_MAPPING["http_methods"]["paths"],
        "locale": PAYLOAD_MAPPING["locale"]["paths"],
        "upload": PAYLOAD_MAPPING["upload"]["paths"],
        "unicode": PAYLOAD_MAPPING["unicode"]["paths"],
        "uri_hex": PAYLOAD_MAPPING["uri_hex"]["paths"],
        "php_magic": PAYLOAD_MAPPING["php_magic"]["paths"],
        "ibmmq": PAYLOAD_MAPPING["ibmmq"]["paths"],
    },
}


def get_payload_for_parameter(param_name: str, param_type: str = "string") -> dict:
    """
    根據參數名稱和類型智能選擇 payload 字典
    """
    param_name_lower = param_name.lower()
    param_type_lower = param_type.lower()

    for payload_type, config in PAYLOAD_MAPPING.items():
        if "keywords" in config and any(keyword in param_name_lower for keyword in config["keywords"]):
            if "param_types" in config and param_type_lower in config["param_types"]:
                return {
                    "type": payload_type,
                    "paths": config["paths"],
                    "confidence": "high",
                }

    type_mapping = {
        "integer": "numbers",
        "number": "numbers",
        "boolean": "boolean",
        "json": "structured_data",
        "xml": "structured_data",
        "date": "dates",
        "float": "amounts",
        "file": "upload",
    }

    if param_type_lower in type_mapping:
        mapped_type = type_mapping[param_type_lower]
        if mapped_type in PAYLOAD_MAPPING:
            return {
                "type": mapped_type,
                "paths": PAYLOAD_MAPPING[mapped_type]["paths"],
                "confidence": "medium",
            }

    return {
        "type": "xss",
        "paths": PAYLOAD_MAPPING["xss"]["paths"],
        "confidence": "low",
    }


def get_payload_structure_for_category(category: str) -> dict:
    """
    根據類別獲取 payload 結構
    """
    return PAYLOAD_STRUCTURE.get(f"{category}_payloads", {})
