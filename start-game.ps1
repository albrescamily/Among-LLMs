$session = "amongus"
$project = "C:\projects\among-llms\amongUs"
$python = "C:\projects\among-llms\.venv\Scripts\python.exe"
$players = 4

psmux kill-session -t $session 2>$null

psmux new-session -d -s $session -n server

psmux send-keys `
    -t "${session}:server" `
    "cd '$project\src'; & '$python' server.py" Enter

for ($i = 1; $i -le $players; $i++) {

    $name = "player-$i"

    psmux new-window `
        -t $session `
        -n $name `
        -d

    psmux send-keys `
        -t "${session}:${name}" `
        "cd '$project\src'; & '$python' main.py" Enter
}

psmux attach -t $session