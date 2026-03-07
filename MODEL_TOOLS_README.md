# Django Model Reflection Tools

這套工具可以幫助你自動分析和輸出 Django 模型定義，並生成自動反射註解。

## 工具概述

### 1. Django Management Commands

#### `export_models` - 基本模型導出工具
```bash
python manage.py export_models --app core --format markdown --include-fields --include-methods
```

**功能：**
- 導出指定 app 的所有模型
- 支援多種輸出格式：markdown, json, yaml
- 可選擇包含字段詳細信息和方法
- 自動生成模型關係圖和文檔

**參數：**
- `--app`: 指定 app 名稱（預設：core）
- `--format`: 輸出格式（markdown/json/yaml）
- `--include-fields`: 包含詳細字段信息
- `--include-methods`: 包含模型方法

#### `model_reflector` - 高級模型反射工具
```bash
python manage.py model_reflector --app core --output-dir ./model_docs --generate-admin --generate-serializers --generate-factories --generate-tests --include-inheritance
```

**功能：**
- 全面的模型分析和文檔生成
- 自動生成 Django Admin 配置
- 自動生成 DRF 序列化器
- 自動生成 Factory Boy 工廠
- 自動生成測試模板
- 模型繼承關係分析

**參數：**
- `--app`: 指定 app 名稱
- `--output-dir`: 輸出目錄
- `--generate-admin`: 生成 Django Admin 配置
- `--generate-serializers`: 生成 DRF 序列化器
- `--generate-factories`: 生成 Factory Boy 工廠
- `--generate-tests`: 生成測試模板
- `--include-inheritance`: 包含繼承分析

### 2. Standalone Model Reflector

當 Django 環境有問題或需要獨立運行時，使用此工具：

```bash
python standalone_model_reflector.py --models-dir apps/core/models --output-dir ./model_analysis --format both
```

**功能：**
- 不依賴 Django 環境
- 使用 AST 解析模型文件
- 生成 Markdown 和 JSON 格式輸出
- 自動識別 Django 模型
- 詳細的字段和方法分析

## 使用範例

### 基本使用

1. **快速查看模型概覽：**
```bash
python standalone_model_reflector.py --models-dir apps/core/models --format markdown
```

2. **生成完整文檔：**
```bash
python standalone_model_reflector.py --models-dir apps/core/models --output-dir ./docs --format both
```

3. **使用 Django 管理命令：**
```bash
python manage.py export_models --app core --include-fields --include-methods
```

### 高級使用

1. **生成完整的開發套件：**
```bash
python manage.py model_reflector --app core --generate-admin --generate-serializers --generate-factories --generate-tests
```

2. **分析特定模型目錄：**
```bash
python standalone_model_reflector.py --models-dir path/to/your/models --output-dir ./analysis
```

## 輸出文件說明

### Markdown 文檔 (`models_documentation.md`)
- 模型概覽和統計信息
- 詳細的字段表格
- 方法列表和文檔
- 繼承關係分析
- 目錄和導航

### JSON 數據 (`models_data.json`)
- 結構化的模型數據
- 可用於程序化處理
- 包含所有模型元數據

### Django Admin (`admin.py`)
- 自動生成的 Admin 配置
- 智能字段選擇
- 過濾器和搜索配置

### DRF 序列化器 (`serializers.py`)
- 完整的序列化器定義
- 支援所有模型字段
- 標準的 Meta 配置

### Factory Boy 工廠 (`factories.py`)
- 自動生成的測試數據工廠
- 智能字段類型推斷
- Faker 集成

### 測試模板 (`test_models.py`)
- 基本的模型測試
- 創建和驗證測試
- 可擴展的測試結構

## 分析結果

根據你的 `apps/core/models` 目錄，工具分析出：

- **總計 28 個模型**
- **245 個字段**
- **23 個方法**
- **7 個模型文件**

### 模型分布：
- `assets.py`: 6 個模型（Target, Seed, IP, Port, Subdomain 等）
- `url_assets.py`: 10 個模型（URLResult, Form, Endpoint 等）
- `Vulnerability.py`: 1 個模型（Vulnerability）
- `scans_record_modles.py`: 5 個模型（NmapScan, NucleiScan 等）
- `js_files.py`: 2 個模型（JavaScriptFile, ExtractedJS）
- `analyze_ai_models.py`: 3 個模型（AI 分析模型）
- `techstack.py`: 1 個模型（TechStack）

## 自動反射功能

工具會自動分析並生成：

1. **字段類型推斷**
   - 自動識別 CharField, TextField, IntegerField 等
   - 提取字段參數（max_length, null, blank 等）
   - 識別關係字段（ForeignKey, ManyToManyField）

2. **關係映射**
   - 外鍵關係分析
   - 反向關係識別
   - 相關名稱提取

3. **方法分析**
   - 自動提取模型方法
   - 參數和返回值分析
   - 文檔字符串提取

4. **繼承分析**
   - 模型繼承鏈分析
   - 父類和子類關係
   - 抽象模型識別

## 自定義和擴展

### 添加新的輸出格式
可以在 `export_models` 命令中添加新的格式支持：

```python
elif output_format == 'custom_format':
    self.export_custom_format(models_list, include_fields, include_methods)
```

### 擴展字段分析
可以在 `get_field_attributes` 方法中添加更多字段屬性分析：

```python
if hasattr(field, 'custom_attribute'):
    attrs['custom_attribute'] = field.custom_attribute
```

### 自定義模板
可以修改生成的代碼模板以符合你的項目風格。

## 故障排除

### 常見問題

1. **Django 環境問題**
   - 使用 `standalone_model_reflector.py` 作為替代方案
   - 確保 Django 設置正確

2. **模型識別問題**
   - 檢查模型是否正確繼承 `models.Model`
   - 確認導入語句正確

3. **輸出格式問題**
   - 檢查輸出目錄權限
   - 確認格式參數正確

### 調試技巧

1. **啟用詳細輸出：**
```bash
python standalone_model_reflector.py --models-dir apps/core/models --format both --verbose
```

2. **檢查 AST 解析：**
   - 查看生成的 JSON 文件
   - 驗證模型識別是否正確

## 貢獻

歡迎提交問題報告和功能請求！這些工具是開源的，可以根據你的具體需求進行定制。
