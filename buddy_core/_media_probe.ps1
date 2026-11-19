Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

$type = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime]
$manager = Await ($type::RequestAsync()) $type

Write-Output "=== SESSIONS ==="
foreach ($s in $manager.GetSessions()) {
    $info = $s.GetPlaybackInfo()
    Write-Output ("AUMID={0} | Status={1}" -f $s.SourceAppUserModelId, $info.PlaybackStatus)
}

$apple = $manager.GetSessions() | Where-Object { $_.SourceAppUserModelId -like "*AppleMusic*" } | Select-Object -First 1
if ($apple) {
    Write-Output "=== APPLE MUSIC METHODS ==="
    $apple | Get-Member -MemberType Method | ForEach-Object { Write-Output $_.Name }
} else {
    Write-Output "=== APPLE MUSIC SESSION NOT FOUND ==="
}
