# Starts the server plus -Humans player windows (menu, keyboard) and -Agents headless
# agents, each in its own psmux window. Humans and agents share the five colours.
param(
    [int]$Humans = 1,
    [int]$Agents = 3
)

$session = "amongus"
$project = "C:\projects\among-llms\amongUs"
$python = "C:\projects\among-llms\.venv\Scripts\python.exe"
$colours = @("Red", "Blue", "Orange", "Yellow", "Green")
$total = $Humans + $Agents

if ($total -lt 1 -or $total -gt $colours.Count) {
    Write-Error "Humans + Agents must be between 1 and $($colours.Count), got $total"
    exit 1
}

psmux kill-session -t $session 2>$null

psmux new-session -d -s $session -n server

psmux send-keys `
    -t "${session}:server" `
    "cd '$project\src'; & '$python' server.py --players $total" Enter

for ($i = 1; $i -le $Humans; $i++) {

    $name = "player-$i"

    psmux new-window `
        -t $session `
        -n $name `
        -d

    psmux send-keys `
        -t "${session}:${name}" `
        "cd '$project\src'; & '$python' main.py" Enter
}

# agents connect the moment they start, so give the server time to listen first
Start-Sleep -Seconds 3

for ($i = 1; $i -le $Agents; $i++) {

    $name = "agent-$i"
    # hand agents the colours from the end of the list, leaving the first ones to humans
    $colour = $colours[$colours.Count - $i]

    psmux new-window `
        -t $session `
        -n $name `
        -d

    psmux send-keys `
        -t "${session}:${name}" `
        "cd '$project\src'; & '$python' -m agents --colour $colour --name $name" Enter
}

psmux attach -t $session
