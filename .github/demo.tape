Output .github/assets/demo.gif

Set Shell "bash"
Set FontSize 13
Set Width 1200
Set Height 640
Set Theme "Catppuccin Mocha"
Set Padding 20

Type "# FlowIndex demo"
Enter
Sleep 500ms
Type "cd examples/python_fastapi_app && rm -rf .flowindex"
Enter
Sleep 500ms
Type "../../.venv/bin/flowindex init --here"
Enter
Sleep 2s
Type "../../.venv/bin/flowindex scan"
Enter
Sleep 3s
Type "../../.venv/bin/flowindex context 'fix duplicate payments when webhook retries'"
Enter
Sleep 4s
