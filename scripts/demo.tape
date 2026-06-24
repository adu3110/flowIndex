# FlowIndex demo — render with: vhs demo.tape
# Install: brew install vhs

Output demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1100
Set Height 620
Set Theme "Catppuccin Mocha"

Hide
Type "cd examples/python_fastapi_app"
Enter
Type "flowindex init --here"
Enter
Sleep 2s
Type "flowindex scan"
Enter
Sleep 2s
Type "flowindex context 'fix duplicate payments when webhook retries'"
Enter
Sleep 3s
Show
