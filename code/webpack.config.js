//@ts-check

'use strict';

const path = require('path')

//@ts-check
/** @typedef {import('webpack').Configuration} WebpackConfig **/

// Configuration for the "main" version of the VSCode extension
/**@type WebpackConfig */
const nodeConfig = {
    target: 'node',
    mode: 'none',
    entry: './src/node/extension.ts',
    output: {
        path: path.resolve(__dirname, 'dist', 'node'),
        filename: 'extension.js',
        libraryTarget: 'commonjs2',
    },
    externals: {
        vscode: "commonjs vscode"
    },
    resolve: {
        extensions: ['.ts', '.js']
    },
    module: {
        rules: [
            {
                test: /.ts$/,
                exclude: /node_modules/,
                use: [{ loader: 'ts-loader' }]
            }
        ]
    },
    devtool: 'source-map',
    infrastructureLogging: {
        level: 'log',
    },
}
module.exports = [nodeConfig]
