#!/bin/bash

# 检查参数数量
if [ "$#" -ne 2 ]; then
    echo "使用方法: $0 <文件名> <分割大小(MB)>"
    echo "例如: $0 large_file.zip 50"
    exit 1
fi

FILE_NAME="$1"
SPLIT_SIZE_MB="$2"
SPLIT_SIZE_BYTES="${SPLIT_SIZE_MB}M"
OUTPUT_PREFIX="${FILE_NAME}.part"

# 检查文件是否存在
if [ ! -f "$FILE_NAME" ]; then
    echo "错误：文件 '$FILE_NAME' 不存在。"
    exit 1
fi

echo "正在将文件 '$FILE_NAME' 分割为 '$SPLIT_SIZE_MB'MB 大小..."

# 执行分割命令
split -b "$SPLIT_SIZE_BYTES" "$FILE_NAME" "$OUTPUT_PREFIX"

# 检查分割是否成功
if [ $? -eq 0 ]; then
    echo "文件分割成功！"
    echo "分割后的文件名为："
    ls -lh "${OUTPUT_PREFIX}"*
    echo ""
    echo "---"
    echo "合并命令："
    echo "cat ${OUTPUT_PREFIX}* > ${FILE_NAME}"
else
    echo "文件分割失败，请检查错误。"
    exit 1
fi

exit 0
