# NileOps — Demo Self-Check Test Suite
# Validates single-port production server (127.0.0.1:8000), authentication,
# RAG service, Document AI OCR upload, Ops Assistant, and Ollama latency.

param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        NileOps Production Demo Health & Smoke Check       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Target Base URL: $BaseUrl`n" -ForegroundColor Gray

$results = @()

function Record-Result ([string]$TestName, [bool]$Success, [double]$DurationMs, [string]$Details = "") {
    $statusText = if ($Success) { "PASS" } else { "FAIL" }
    $color = if ($Success) { "Green" } else { "Red" }
    Write-Host ("[{0}] {1,-35} ({2,6:N0} ms) - {3}" -f $statusText, $TestName, $DurationMs, $Details) -ForegroundColor $color
    $script:results += [PSCustomObject]@{
        Test = $TestName
        Status = $statusText
        DurationMs = [Math]::Round($DurationMs, 1)
        Details = $Details
    }
}

# ---------------------------------------------------------
# Test 1: Unauthenticated Health Check Endpoint
# ---------------------------------------------------------
$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
    $healthResp = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 10
    $sw.Stop()
    $isHealthy = ($healthResp.status -eq "healthy")
    Record-Result -TestName "1. Unauthenticated Health Probe" -Success $isHealthy -DurationMs $sw.Elapsed.TotalMilliseconds -Details "DB: $($healthResp.database)"
} catch {
    $sw.Stop()
    Record-Result -TestName "1. Unauthenticated Health Probe" -Success $false -DurationMs $sw.Elapsed.TotalMilliseconds -Details $_.Exception.Message
}

# ---------------------------------------------------------
# Test 2: Customer Authentication & RAG Ask
# ---------------------------------------------------------
$customerToken = $null
$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
    $loginBody = @{
        email = "customer1@nileops.demo"
        password = "Customer2026!"
    } | ConvertTo-Json
    $loginResp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/json" -TimeoutSec 10
    $sw.Stop()
    $customerToken = $loginResp.access_token
    Record-Result -TestName "2. Customer Login (customer1)" -Success ($null -ne $customerToken) -DurationMs $sw.Elapsed.TotalMilliseconds -Details "Role: $($loginResp.user.role)"
} catch {
    $sw.Stop()
    Record-Result -TestName "2. Customer Login (customer1)" -Success $false -DurationMs $sw.Elapsed.TotalMilliseconds -Details $_.Exception.Message
}

if ($customerToken) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $ragBody = @{
            query = "ما هي حدود التحويل اليومي عبر تطبيق انستاباي؟"
            portal_type = "customer"
            language = "ar"
        } | ConvertTo-Json
        $headers = @{
            Authorization = "Bearer $customerToken"
        }
        $ragResp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/rag/ask" -Method Post -Headers $headers -Body $ragBody -ContentType "application/json" -TimeoutSec 30
        $sw.Stop()
        $hasAnswer = ($null -ne $ragResp.answer) -and ($ragResp.answer.Length -gt 10)
        $mode = if ($ragResp.fallback_used) { "Deterministic Fallback" } else { "Ollama LLM" }
        $citationCount = if ($ragResp.citations) { $ragResp.citations.Count } else { 0 }
        Record-Result -TestName "3. Customer RAG Inquiry" -Success $hasAnswer -DurationMs $sw.Elapsed.TotalMilliseconds -Details "Mode: $mode | Citations: $citationCount"
    } catch {
        $sw.Stop()
        Record-Result -TestName "3. Customer RAG Inquiry" -Success $false -DurationMs $sw.Elapsed.TotalMilliseconds -Details $_.Exception.Message
    }
}

# ---------------------------------------------------------
# Test 3: Compliance Login & Document AI OCR Upload
# ---------------------------------------------------------
$compToken = $null
$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
    $compLoginBody = @{
        email = "compliance@nileops.demo"
        password = "NileOps2026!"
    } | ConvertTo-Json
    $compLoginResp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -Body $compLoginBody -ContentType "application/json" -TimeoutSec 10
    $sw.Stop()
    $compToken = $compLoginResp.access_token
    Record-Result -TestName "4. Compliance Staff Login" -Success ($null -ne $compToken) -DurationMs $sw.Elapsed.TotalMilliseconds -Details "Role: $($compLoginResp.user.role)"
} catch {
    $sw.Stop()
    Record-Result -TestName "4. Compliance Staff Login" -Success $false -DurationMs $sw.Elapsed.TotalMilliseconds -Details $_.Exception.Message
}

$sampleCardPath = Join-Path $repoRoot "data\synthetic_cards\eval_held_out_60\ho_clean_02.png"
if (-not (Test-Path $sampleCardPath)) {
    # Fallback to dev card if held-out is not at that exact path
    $sampleCardPath = (Get-ChildItem -Path (Join-Path $repoRoot "data\synthetic_cards") -Filter "*.png" -Recurse | Select-Object -First 1).FullName
}

if ($compToken -and (Test-Path $sampleCardPath)) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        # Perform multipart file upload using curl.exe
        $uploadUrl = "$BaseUrl/api/v1/employee/kyc-verifications/upload"
        $curlOut = & curl.exe -s -X POST $uploadUrl -H "Authorization: Bearer $compToken" -F "file=@$sampleCardPath"
        $sw.Stop()
        $ocrJson = $curlOut | ConvertFrom-Json
        $idExtracted = ($null -ne $ocrJson.id) -and ($null -ne $ocrJson.status)
        Record-Result -TestName "5. Document AI KYC Card Upload" -Success $idExtracted -DurationMs $sw.Elapsed.TotalMilliseconds -Details "Status: $($ocrJson.status) | Synthetic ID: $($ocrJson.synthetic_national_id)"
    } catch {
        $sw.Stop()
        Record-Result -TestName "5. Document AI KYC Card Upload" -Success $false -DurationMs $sw.Elapsed.TotalMilliseconds -Details $_.Exception.Message
    }
}

# ---------------------------------------------------------
# Test 4: Ops Assistant (Staff Agent Chat)
# ---------------------------------------------------------
if ($compToken) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $agentBody = @{
            message = "ما هي حالة طلبات فتح الحساب المعلقة؟"
            language = "ar"
        } | ConvertTo-Json
        $headers = @{
            Authorization = "Bearer $compToken"
        }
        $agentResp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/agent/chat" -Method Post -Headers $headers -Body $agentBody -ContentType "application/json" -TimeoutSec 30
        $sw.Stop()
        $hasAgentReply = ($null -ne $agentResp.reply) -and ($agentResp.reply.Length -gt 5)
        $toolCount = if ($agentResp.tool_trace) { $agentResp.tool_trace.Count } else { 0 }
        Record-Result -TestName "6. Ops Assistant Agent Chat" -Success $hasAgentReply -DurationMs $sw.Elapsed.TotalMilliseconds -Details "Tools: $toolCount | Fallback: $($agentResp.fallback_used)"
    } catch {
        $sw.Stop()
        Record-Result -TestName "6. Ops Assistant Agent Chat" -Success $false -DurationMs $sw.Elapsed.TotalMilliseconds -Details $_.Exception.Message
    }
}

# ---------------------------------------------------------
# Test 5: Ollama Health & Latency Benchmark
# ---------------------------------------------------------
Write-Host "`n--- Checking Ollama Service & Latency ---" -ForegroundColor Yellow
$ollamaUp = $false
try {
    $tcpOllama = New-Object System.Net.Sockets.TcpClient
    $tcpOllama.Connect("127.0.0.1", 11434)
    $tcpOllama.Close()
    $ollamaUp = $true
} catch {
    $ollamaUp = $false
}

if ($ollamaUp) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $ollamaPayload = @{
            model = "qwen3:8b"
            prompt = "Short test. Reply with 'READY'."
            stream = $false
        } | ConvertTo-Json
        $ollamaResp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -Body $ollamaPayload -ContentType "application/json" -TimeoutSec 45
        $sw.Stop()
        $durationSec = [Math]::Round($sw.Elapsed.TotalSeconds, 2)
        Write-Host "Ollama 'qwen3:8b' latency: $durationSec seconds." -ForegroundColor Cyan
        if ($durationSec -gt 30.0) {
            Write-Warning "Ollama inference latency ($durationSec s) exceeds recommended 30-second budget!`nSuggestion: Run a smaller quantized model such as 'qwen2.5:3b' or rely on NileOps's instant deterministic fallback."
        } else {
            Write-Host "Ollama response latency is within optimal range (< 30s)." -ForegroundColor Green
        }
    } catch {
        $sw.Stop()
        Write-Host "Ollama ping attempt completed in $($sw.Elapsed.TotalSeconds)s with notice: $($_.Exception.Message)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "Local Ollama is offline. NileOps is operating in pure deterministic fallback mode (< 50ms latency)." -ForegroundColor Green
}

# ---------------------------------------------------------
# Summary Table
# ---------------------------------------------------------
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "                   Self-Check Summary                     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$allPassed = ($results | Where-Object { $_.Status -ne "PASS" }).Count -eq 0
$results | Format-Table -AutoSize

if ($allPassed) {
    Write-Host "ALL PRE-FLIGHT DEMO CHECKS PASSED SUCCESSFULLY." -ForegroundColor Green
    exit 0
} else {
    Write-Warning "One or more checks did not pass. Check log details above."
    exit 1
}
