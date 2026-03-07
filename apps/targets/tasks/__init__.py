from celery import shared_task # 從 celery 模塊導入 shared_task 裝飾器
import time # 導入 time 模塊，用於時間相關操作（例如延遲）


@shared_task # 將此函數註冊為一個 Celery 共享任務，使其可以在後台異步執行
def add(x, y): # 定義一個名為 add 的函數，接收兩個參數 x 和 y
    # 一個最簡單的測試任務 # 這是原始註釋，保持不變
    print(f"正在執行異步任務： {x} + {y}...") # 打印一條消息，指示任務正在執行
    time.sleep(5)  # 模擬一個耗時 5 秒的操作 # 讓任務暫停執行 5 秒，模擬耗時操作
    result = x + y # 計算 x 和 y 的和，將結果存儲在 result 變量中
    print(f"異步任務完成！結果是： {result}") # 打印任務完成的消息和計算結果
    return result # 返回計算得到的結果