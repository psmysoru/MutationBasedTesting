const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Mutation Test Generator is now active!');

    // Register command to generate tests
    let disposable = vscode.commands.registerCommand('mutation-test-generator.generateTests', async function () {
        try {
            // Get configuration
            const config = vscode.workspace.getConfiguration('mutationTestGenerator');
            let sourceDir = config.get('sourceDir');
            let testDir = config.get('testDir');
            
            // If not set in config, ask the user
            if (!sourceDir) {
                sourceDir = await vscode.window.showInputBox({
                    prompt: 'Enter the source directory path',
                    placeHolder: 'e.g., ./src'
                });
                if (!sourceDir) return; // User cancelled
            }
            
            if (!testDir) {
                testDir = await vscode.window.showInputBox({
                    prompt: 'Enter the test directory path',
                    placeHolder: 'e.g., ./tests'
                });
                if (!testDir) return; // User cancelled
            }
            
            // Create output channel to show results
            const outputChannel = vscode.window.createOutputChannel('Mutation Test Generator');
            outputChannel.show();
            outputChannel.appendLine('Starting mutation-guided test generation...');
            outputChannel.appendLine(`Source directory: ${sourceDir}`);
            outputChannel.appendLine(`Test directory: ${testDir}`);
            
            // Run the Python script in a separate process
            const pythonScriptPath = path.join(context.extensionPath, 'scripts', 'mutation_guided_test_generator.py');
            
            // Create shell command based on platform
            const isWindows = process.platform === 'win32';
            const pythonCmd = isWindows ? 'python' : 'python3';
            
            // Spawn process
            const process = spawn(pythonCmd, [
                pythonScriptPath,
                '--source_dir', sourceDir,
                '--test_dir', testDir,
                '--vscode_path', getVSCodePath()
            ]);
            
            // Handle output
            process.stdout.on('data', (data) => {
                outputChannel.appendLine(data.toString());
            });
            
            process.stderr.on('data', (data) => {
                outputChannel.appendLine(`ERROR: ${data}`);
            });
            
            process.on('close', (code) => {
                if (code === 0) {
                    outputChannel.appendLine('\nTest generation completed successfully!');
                    vscode.window.showInformationMessage('Mutation test generation completed successfully!');
                } else {
                    outputChannel.appendLine(`\nTest generation failed with code ${code}`);
                    vscode.window.showErrorMessage('Mutation test generation failed. See output for details.');
                }
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Error: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * Get the VS Code executable path
 */
function getVSCodePath() {
    // VS Code's executable path is accessible via process.execPath
    return process.execPath;
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}
