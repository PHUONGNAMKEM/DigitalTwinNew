# Script để chuyển sang Java 17
# Sử dụng: .\set_java17.ps1

$JAVA17_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"

$env:JAVA_HOME = $JAVA17_HOME
$env:PATH = "$JAVA17_HOME\bin;" + ($env:PATH -replace [regex]::Escape("C:\Program Files\Eclipse Adoptium\jdk-11.0.28.6-hotspot\bin;"), "")

Write-Host "✅ Đã chuyển sang Java 17" -ForegroundColor Green
java -version
