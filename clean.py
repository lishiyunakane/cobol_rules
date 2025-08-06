import glob
import os

num_files = 1

# 删除所有现有的 chunk_*.txt 文件
for file in glob.glob("chunk_*.txt"):
    print(f"🗑 删除：{file}")
    os.remove(file)

# 创建新的空 chunk_001.txt 到 chunk_00N.txt 文件
for i in range(1, num_files + 1):
    filename = f"chunk_{i:03}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        pass  # 创建空文件
    print(f"✅ 生成：{filename}")
