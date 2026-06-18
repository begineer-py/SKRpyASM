import json
import os
import re


def split_to_semantic_files(input_file, output_dir="fingerprints"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for pkg_name, content in data.items():
        # 把檔名裡不合法的字元換掉 (例如 / 換成 _)
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", pkg_name)
        file_path = os.path.join(output_dir, f"{safe_name}.json")

        # 保持原有的結構：{ "套件名": { 內容 } }
        output_data = {pkg_name: content}

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"已生成: {file_path}")


if __name__ == "__main__":
    # 這裡填你原始的那個大 JSON 檔名
    split_to_semantic_files("jsrepository-v5.json")
