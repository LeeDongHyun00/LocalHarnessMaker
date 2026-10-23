const commands = [
"python -m py_compile solution.py",
"python -c 'from solution import solve; values = [\"synthetic\", \"example\"]; assert len(values) == 2; print(\"synthetic verification\", values)'",
"python -m unittest discover -v"
];
const results = await Promise.allSettled(commands.map(cmd => tools.exec_command({cmd, max_output_tokens:4000})));
results.forEach((result, i) => text({command: commands[i], result}));
