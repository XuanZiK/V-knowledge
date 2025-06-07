# 创建目录
New-Item -ItemType Directory -Force -Path "qdrant"
Set-Location qdrant

# 下载Qdrant
$url = "https://github.com/qdrant/qdrant/releases/download/v1.1.1/qdrant-x86_64-pc-windows-msvc.zip"
$output = "qdrant.zip"
Invoke-WebRequest -Uri $url -OutFile $output

# 解压文件
Expand-Archive -Path $output -DestinationPath .
Remove-Item $output

# 运行Qdrant
.\qdrant.exe 