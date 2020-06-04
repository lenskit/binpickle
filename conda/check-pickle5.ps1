write-host "scanning for outputs"
$outs = (conda build --output pickle5 | split-path -Leaf)
$needed = $outs

foreach ($out in $outs) {
    write-host "output package: $out"
}

write-host "scanning for packages"
$result = (conda search -c lenskit --info --json pickle5 |ConvertFrom-Json)

foreach ($p in $result.pickle5) {
    $pfn = $p.fn
    write-host "published package: $pfn"
    $needed = $needed | where-object { $_ -ne $pfn }
}

write-host "remaining to build: $needed"
if ($needed.Length) {
    write-host "::set-output name=up_to_date::false"
} else {
    write-host "::set-output name=up_to_date::true"
}
