# HTTP Sender Payload Mapping 配置文檔

## 概述

本文檔描述了 `apps/http_sender` 模組中增強的 payload 映射系統，該系統基於 SecLists 提供智能的參數到字典映射。

## 文件結構

```
apps/http_sender/
├── payload_mapping.py          # 核心映射配置
├── tasks/fuzzer.py            # 增強的 fuzzer 邏輯
└── schemas.py                 # API schema 定義
```

## Payload 類別分類

### 1. 注入類 Payloads (`injection_payloads`)

#### SQL Injection (`sqli`)
- **關鍵字**: `id`, `user`, `admin`, `login`, `search`, `query`, `filter`, `data`
- **參數類型**: `integer`, `string`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Fuzzing/SQLi/SQLi.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/SQLi/GreedySQLi.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/SQLi/Error-Based-SQLi.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/SQLi/Union-Based-SQLi.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/SQLi/Boolean-Based-SQLi.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/SQLi/Time-Based-SQLi.txt`

#### XSS (`xss`)
- **關鍵字**: `comment`, `message`, `content`, `description`, `name`, `title`, `search`
- **參數類型**: `string`, `text`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Fuzzing/XSS/XSS-RSnake.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/XSS/PortSwigger-XSS.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/XSS/HTML-Injection.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/XSS/Javascript-Injection.txt`

#### Command Injection (`command_injection`)
- **關鍵字**: `cmd`, `command`, `exec`, `run`, `execute`, `file`, `path`
- **參數類型**: `string`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Fuzzing/Command-Injection.txt`
  - `/usr/share/wordlists/SecLists/Payloads/Command-Injection.txt`

#### File Inclusion (`file_inclusion`)
- **關鍵字**: `file`, `path`, `dir`, `folder`, `include`, `page`, `document`
- **參數類型**: `string`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Fuzzing/LFI/LFI.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/LFI/PathTraversal.txt`
  - `/usr/share/wordlists/SecLists/Discovery/Web-Content/common.txt`

### 2. 認證類 Payloads (`authentication_payloads`)

#### 用戶名/密碼 (`credentials`)
- **關鍵字**: `password`, `pass`, `pwd`, `login`, `user`, `username`
- **參數類型**: `string`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Passwords/Common-Credentials/10-million-password-list-top-1000.txt`
  - `/usr/share/wordlists/SecLists/Usernames/names.txt`
  - `/usr/share/wordlists/SecLists/Usernames/xato-net-10-million-usernames.txt`

#### 郵箱 (`email`)
- **關鍵字**: `email`, `mail`, `username`, `user`
- **參數類型**: `string`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Discovery/Web-Content/common-emails.txt`
  - `/usr/share/wordlists/SecLists/Usernames/names.txt`

### 3. 發現類 Payloads (`discovery_payloads`)

#### 目錄/文件發現 (`discovery`)
- **關鍵字**: `dir`, `directory`, `folder`, `path`, `file`
- **參數類型**: `string`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Discovery/Web-Content/common.txt`
  - `/usr/share/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt`
  - `/usr/share/wordlists/SecLists/Discovery/Web-Content/raft-medium-directories.txt`

#### API 密鑰 (`api_keys`)
- **關鍵字**: `key`, `token`, `api`, `secret`, `auth`, `bearer`
- **參數類型**: `string`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Discovery/Web-Content/api/api-keys.txt`
  - `/usr/share/wordlists/SecLists/Discovery/Web-Content/api/tokens.txt`

### 4. 數據類型 Payloads (`data_type_payloads`)

#### 數字 (`numbers`)
- **關鍵字**: `id`, `num`, `number`, `count`, `page`, `limit`, `offset`
- **參數類型**: `integer`, `number`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Fuzzing/numbers.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/ids.txt`

#### 布爾值 (`boolean`)
- **關鍵字**: `bool`, `boolean`, `flag`, `enabled`, `disabled`, `active`, `status`
- **參數類型**: `boolean`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Fuzzing/booleans.txt`

#### 結構化數據 (`structured_data`)
- **關鍵字**: `json`, `xml`, `data`, `config`, `settings`
- **參數類型**: `json`, `xml`, `object`
- **字典路徑**:
  - `/usr/share/wordlists/SecLists/Fuzzing/json.txt`
  - `/usr/share/wordlists/SecLists/Fuzzing/xml.txt`

## 智能匹配算法

### 匹配優先級

1. **高置信度** - 關鍵字精確匹配 + 參數類型匹配
2. **中置信度** - 僅參數類型匹配
3. **低置信度** - 默認字符串處理

### 匹配流程

```python
def get_payload_for_parameter(param_name: str, param_type: str = "string") -> dict:
    """
    1. 精確關鍵字匹配
    2. 類型匹配  
    3. 默認字符串處理
    """
```

## 使用示例

### 在 Fuzzer 中的應用

```python
# 智能參數匹配
payload_info = get_payload_for_parameter(p_key, p_type)

if payload_info["confidence"] in ["high", "medium"]:
    target_param = param
    selected_wordlist = payload_info["paths"][0]
    logger.info(f"智能匹配: 參數 [{p_key}] -> 類型 [{payload_info['type']}] -> 置信度 [{payload_info['confidence']}]")
```

### .payload 字典結構

```python
PAYLOAD_STRUCTURE = {
    "injection_payloads": {
        "sqli": [...],
        "xss": [...],
        "command_injection": [...],
        "file_inclusion": [...]
    },
    "authentication_payloads": {
        "usernames": [...],
        "passwords": [...],
        "emails": [...]
    },
    "discovery_payloads": {
        "directories": [...],
        "files": [...],
        "api_endpoints": [...]
    },
    "data_type_payloads": {
        "numbers": [...],
        "booleans": [...],
        "strings": [...],
        "structured": [...]
    }
}
```

## 配置擴展

### 添加新的 Payload 類型

1. 在 `PAYLOAD_MAPPING` 中添加新條目
2. 定義關鍵字和參數類型
3. 指定 SecLists 路徑
4. 更新 `PAYLOAD_STRUCTURE`

### 自定義字典路徑

```python
SECLISTS_BASE = "/usr/share/wordlists/SecLists"  # 可修改為自定義路徑
```

## 日誌輸出

系統會記錄匹配過程：
```
智能匹配: 參數 [user_id] -> 類型 [numbers] -> 置信度 [medium]
選定 Fuzz 目標參數: [user_id], 類型: [integer]
使用字典: /usr/share/wordlists/SecLists/Fuzzing/numbers.txt
```

## 注意事項

1. 確保 SecLists 已正確安裝在指定路徑
2. 字典文件必須存在且可讀
3. 根據目標環境調整匹配規則
4. 定期更新 SecLists 以獲得最新 payload

## 未來改進

- 支持動態權重調整
- 添加機器學習匹配算法
- 支持自定義 payload 生成
- 集成更多安全測試字典
