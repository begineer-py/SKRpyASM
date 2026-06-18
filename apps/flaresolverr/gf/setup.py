from setuptools import setup, find_packages # 導入 setuptools 模組中的 setup 和 find_packages 函數
import os # 導入 os 模組，用於文件系統操作


# 我們需要讓 patterns 資料夾也跟著一起打包
def find_pattern_files(directory): # 定義一個函數，用於查找指定目錄下的模式文件
    paths = [] # 初始化一個空列表，用於存儲找到的文件路徑
    for path, directories, filenames in os.walk(directory): # 遍歷指定目錄及其子目錄
        for filename in filenames: # 遍歷當前目錄下的所有文件
            if filename.endswith(".json"): # 檢查文件是否以 .json 結尾
                # 我們需要的是相對於 'hacker_gf' 模組的路徑
                paths.append(os.path.join("..", path, filename)) # 將文件路徑添加到列表中，路徑前綴為".."以確保相對正確
    return paths # 返回所有找到的 .json 文件路徑


pattern_files = find_pattern_files("hacker_gf/patterns") # 調用函數查找模式文件，並將結果存儲到 pattern_files 變量中


setup( # 調用 setup 函數，配置打包的詳細信息
    name="hacker_gf", # 定義項目名稱
    version="0.1.0", # 定義項目版本號
    description="A Pure Python, grep-free, spiritual successor to gf, designed for structured output and easy integration.", # 定義項目的簡短描述
    long_description=open("README.md").read(), # 讀取 README.md 文件作為項目的詳細描述
    long_description_content_type="text/markdown", # 指定詳細描述的內容類型為 Markdown
    author="begineer-py",  # 換成你的名字 # 定義項目作者名稱
    author_email="pythonuseful@gmail.com",  # 可選 # 定義項目作者的電子郵件（可選）
    url="https://github.com/begineer-py/hacker_gf", # 定義項目源代碼的 URL
    packages=find_packages(), # 自動查找項目中的所有包
    include_package_data=True, # 包含非代碼文件（如模式文件）在打包中
    package_data={ # 定義需要包含在特定包中的額外數據文件
        "hacker_gf": ["patterns/*.json"], # 指定 hacker_gf 包中包含 patterns 目錄下的所有 .json 文件
    }, # 結束 package_data 定義
    entry_points={ # 定義命令行腳本入口點
        "console_scripts": [ # 指定控制台腳本
            "hacker_gf = hacker_gf.pygf_engine:main", # 將 hacker_gf 命令映射到 hacker_gf.pygf_engine 模組中的 main 函數
        ], # 結束 console_scripts 定義
    }, # 結束 entry_points 定義
    classifiers=[ # 提供額外的分類元數據，幫助用戶了解項目
        "Programming Language :: Python :: 3", # 指明支持的 Python 版本為 3
        "License :: OSI Approved :: MIT License", # 指明項目使用的許可證為 MIT
        "Operating System :: OS Independent", # 指明項目與操作系統無關
        "Topic :: Security", # 將項目歸類為安全相關主題
        "Topic :: Text Processing", # 將項目歸類為文本處理相關主題
    ], # 結束 classifiers 定義
    python_requires=">=3.6", # 指定項目所需的 Python 最低版本
) # 結束 setup 函數調用