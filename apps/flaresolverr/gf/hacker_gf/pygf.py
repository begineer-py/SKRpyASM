import os  # 導入 os 模塊，用於操作文件路徑和系統功能
import sys  # 導入 sys 模塊，用於系統相關的操作，如標準輸入輸出和退出
import json  # 導入 json 模塊，用於處理 JSON 數據
import argparse  # 導入 argparse 模塊，用於解析命令行參數
import re  # 導入 re 模塊，用於正則表達式操作


class PatternAnalyzer:  # 定義 PatternAnalyzer 類，用於分析文本模式
    def __init__(self):  # 類的初始化方法
        self.PATTERNS_DIR = os.path.join(  # 設定模式文件存放的目錄路徑
            os.path.dirname(os.path.abspath(__file__)), "patterns"
        )
        self.patterns_cache = {}  # 初始化一個字典用於快取已載入的模式

    def get_pattern(self, pattern_name):  # 定義獲取模式的方法
        """從快取或檔案載入一個 pattern，避免重複讀取"""
        if pattern_name in self.patterns_cache:  # 如果模式已在快取中
            return self.patterns_cache[pattern_name]  # 直接返回快取中的模式

        pattern_file = os.path.join(
            self.PATTERNS_DIR, f"{pattern_name}.json"
        )  # 構建模式文件的完整路徑
        try:  # 嘗試打開和解析模式文件
            with open(pattern_file, "r") as f:  # 以讀取模式打開文件
                pat_data = json.load(f)  # 載入 JSON 數據
                self.patterns_cache[pattern_name] = pat_data  # 將模式數據存入快取
                return pat_data  # 返回模式數據
        except FileNotFoundError:  # 捕獲文件未找到的異常
            raise ValueError(
                f"No such pattern '{pattern_name}'"
            )  # 拋出值錯誤，表示找不到指定的模式
        except json.JSONDecodeError:  # 捕獲 JSON 解碼錯誤的異常
            raise ValueError(
                f"Pattern file '{pattern_file}' is malformed JSON."
            )  # 拋出值錯誤，表示模式文件格式不正確

    def analyze(self, lines, pattern_name):  # 定義分析文本的方法
        """
        核心分析函式。它只負責一件事：拿著資料和規則去分析。
        它不關心資料是從哪來的。
        """
        pat_data = self.get_pattern(pattern_name)  # 獲取指定名稱的模式數據

        flags = pat_data.get("flags", "")  # 從模式數據中獲取旗標，如果沒有則為空字符串
        pattern_str = pat_data.get("pattern")  # 從模式數據中獲取單一正則表達式字符串
        patterns = pat_data.get("patterns")  # 從模式數據中獲取多個正則表達式字符串列表

        if not pattern_str and patterns:  # 如果沒有單一模式字符串但有多個模式列表
            pattern_str = (
                f"({'|'.join(patterns)})"  # 將多個模式組合成一個用 '|' 分隔的正則表達式
            )
        if not pattern_str:  # 如果最終沒有任何模式字符串
            raise ValueError(  # 拋出值錯誤
                f"Pattern file for '{pattern_name}' contains no pattern(s)."
            )

        re_flags = (
            re.IGNORECASE if "i" in flags else 0
        )  # 根據旗標設置正則表達式的選項，'i' 表示忽略大小寫

        try:  # 嘗試編譯正則表達式
            compiled_pattern = re.compile(
                pattern_str, flags=re_flags
            )  # 編譯正則表達式以提高效率
        except re.error as e:  # 捕獲正則表達式編譯錯誤
            raise ValueError(
                f"Invalid regex in '{pattern_name}.json': {e}"
            )  # 拋出值錯誤，表示正則表達式無效

        results = []  # 初始化一個列表用於存儲匹配結果
        only_match_mode = (
            "o" in flags
        )  # 根據旗標判斷是否為只匹配模式，'o' 表示只返回第一個匹配項

        for line_num, line in enumerate(
            lines, 1
        ):  # 遍歷每一行文本，並獲取行號（從1開始）
            iterator = compiled_pattern.finditer(
                line
            )  # 使用編譯過的正則表達式在行中查找所有匹配項
            for match in iterator:  # 遍歷所有匹配項
                results.append(  # 將匹配結果添加到結果列表中
                    {
                        "line": line_num,  # 匹配發生的行號
                        "match": match.group(0),  # 匹配到的完整字符串
                        "start": match.start(),  # 匹配字符串的起始索引
                        "end": match.end(),  # 匹配字符串的結束索引
                    }
                )
                if not only_match_mode:  # 如果不是只匹配模式（即需要所有匹配項）
                    break  # 則跳出內層循環，只處理每行的第一個匹配

        return {  # 返回分析結果
            "pattern": pattern_name,  # 使用的模式名稱
            "matches": results,  # 匹配結果列表
            "count": len(results),  # 匹配到的總數
        }

    def run_all_patterns(self, lines):
        """
        一次性跑完所有 patterns，然後把有找到東西的結果打包回傳。
        """
        # 加上這道防線，免得 PATTERNS_DIR 出錯
        if not hasattr(self, "PATTERNS_DIR") or not os.path.isdir(self.PATTERNS_DIR):
            # 我們不拋異常，只返回一個空列表，讓指揮官能繼續走下去
            logging.getLogger(__name__).error(
                f"FUCK: Pattern directory not found at '{getattr(self, 'PATTERNS_DIR', 'Not Set')}'"
            )
            return []

        all_patterns = sorted(
            [
                p.replace(".json", "")
                for p in os.listdir(self.PATTERNS_DIR)
                if p.endswith(".json")
            ]
        )

        all_results = []
        for p in all_patterns:
            try:
                # 把 analyze 包在 try...except 裡，一個 pattern 壞了不影響其他的
                result = self.analyze(lines, p)
                all_results.append(result)
            except ValueError as e:
                logging.getLogger(__name__).warning(
                    f"Skipping pattern '{p}' due to error: {e}"
                )

        # 只回傳那些真的找到東西的分析結果
        return [res for res in all_results if res["count"] > 0]


def main():  # 定義主函數
    analyzer = PatternAnalyzer()  # 創建 PatternAnalyzer 類的實例

    parser = argparse.ArgumentParser(  # 創建命令行參數解析器
        description="A Python-based analysis engine for text patterns."  # 程序描述
    )
    parser.add_argument(  # 添加命令行參數：模式名稱
        "pattern_name",
        nargs="?",
        help="Pattern to use ('all' for all patterns).",  # 模式名稱，可選，'all'表示所有模式
    )
    parser.add_argument(  # 添加命令行參數：目標文件路徑
        "target_path",
        nargs="?",
        help="Target file path (if not using a pipe).",  # 目標文件路徑，可選，用於直接指定文件
    )
    parser.add_argument(  # 添加命令行參數：列出可用模式
        "-l",
        "--list",
        action="store_true",
        help="List available patterns.",  # '-l'或'--list'，如果存在則為真
    )

    args = parser.parse_args()  # 解析命令行參數

    if args.list:  # 如果設置了 --list 參數
        try:  # 嘗試列出所有可用的模式
            patterns = sorted(  # 獲取並排序所有 .json 模式文件名稱
                [
                    p.replace(".json", "")  # 移除文件擴展名
                    for p in os.listdir(
                        analyzer.PATTERNS_DIR
                    )  # 列出模式目錄下的所有文件
                    if p.endswith(".json")  # 只選擇以 .json 結尾的文件
                ]
            )
            for p in patterns:  # 遍歷並打印每個模式名稱
                print(p)
        except FileNotFoundError:  # 捕獲模式目錄未找到的異常
            print(  # 打印錯誤信息到標準錯誤
                f"FUCK: Pattern directory not found at '{analyzer.PATTERNS_DIR}'",
                file=sys.stderr,
            )
            sys.exit(1)  # 以錯誤碼退出程序
        sys.exit(0)  # 成功退出程序

    if not args.pattern_name:  # 如果沒有提供模式名稱
        parser.print_help()  # 打印幫助信息
        sys.exit(1)  # 以錯誤碼退出程序

    # --- 這就是全新的 I/O 處理邏輯 ---
    lines = []  # 初始化一個空列表用於存儲輸入的行
    input_source = "stdin"  # 默認輸入源為標準輸入
    if not sys.stdin.isatty():  # 如果標準輸入不是終端（表示有管道輸入）
        lines = sys.stdin.readlines()  # 從標準輸入讀取所有行
    elif args.target_path:  # 如果沒有管道輸入，但提供了目標文件路徑
        input_source = args.target_path  # 設定輸入源為目標文件路徑
        try:  # 嘗試打開和讀取文件
            if os.path.isdir(input_source):  # 如果目標路徑是一個目錄
                print(  # 打印錯誤信息
                    f"FUCK: '{input_source}' is a directory. Analysis engine needs a file.",
                    file=sys.stderr,
                )
                sys.exit(1)  # 以錯誤碼退出
            with open(
                input_source, "r", errors="ignore"
            ) as f:  # 以讀取模式打開文件，忽略編碼錯誤
                lines = f.readlines()  # 讀取所有行
        except FileNotFoundError:  # 捕獲文件未找到的異常
            print(
                f"FUCK: Target file not found at '{input_source}'", file=sys.stderr
            )  # 打印錯誤信息
            sys.exit(1)  # 以錯誤碼退出
    else:  # 如果既沒有管道輸入也沒有指定文件路徑
        print(  # 打印錯誤信息
            "FUCK: No input data. Provide a file path or pipe data to stdin.",
            file=sys.stderr,
        )
        sys.exit(1)  # 以錯誤碼退出
    # --- 水已經打好，放在 `lines` 這個水桶裡了 ---

    final_results = {}  # 初始化一個字典用於存儲最終結果
    try:  # 嘗試執行分析
        if args.pattern_name.lower() == "all":  # 如果模式名稱是 'all'
            all_patterns = sorted(  # 獲取所有可用的模式名稱
                [
                    p.replace(".json", "")
                    for p in os.listdir(analyzer.PATTERNS_DIR)
                    if p.endswith(".json")
                ]
            )
            analysis_results = [
                analyzer.analyze(lines, p) for p in all_patterns
            ]  # 對所有模式進行分析
            final_results = {  # 構建包含所有分析結果的字典
                "source": input_source,  # 輸入源
                "analysis": [  # 分析結果列表
                    res
                    for res in analysis_results
                    if res["count"] > 0  # 只保留有匹配結果的項
                ],
            }
        else:  # 如果是單個模式名稱
            final_results = analyzer.analyze(
                lines, args.pattern_name
            )  # 對指定模式進行分析
    except ValueError as e:  # 捕獲分析過程中可能發生的值錯誤
        print(f"ERROR: {e}", file=sys.stderr)  # 打印錯誤信息
        sys.exit(1)  # 以錯誤碼退出

    print(
        json.dumps(final_results, indent=2)
    )  # 將最終結果格式化為 JSON 字符串並打印到標準輸出
    sys.exit(0)  # 成功退出程序


if __name__ == "__main__":  # 判斷是否作為主程序運行
    main()  # 調用主函數
