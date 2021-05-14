//@ts-check

// Originally based on
// https://github.com/microsoft/vscode-extension-samples/blob/cf477847244cf291aa13fa447f1c9cf834f302c8/webpack-sample/webpack.config.js

const path = require('path')

/**@type {import('webpack').Configuration}*/
const config = {
    target: 'node',
    entry: './src/extension.ts',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'extension.js',
        libraryTarget: 'commonjs2',
        devtoolModuleFilenameTemplate: '../[resource-path]'
    },
    devtool: 'source-map',
    externals: {
        canvas: "util", // See [1]
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
                use: [
                    {
                        loader: 'ts-loader',
                        options: {
                            compilerOptions: {
                                "module": "es6"
                            }
                        }
                    }
                ]
            }
        ]
    }
}

module.exports = config

/*
 [1] https://github.com/jsdom/jsdom/issues/2508#issuecomment-777387562

 We don't want or need canvas support, as we only use jsdom to rewrite some
 urls so that external assets load in the webview preview.

 This gets webpack to rewrite the "import canvas" statements to "import util"
 and apparently the library is able to degrade gracefully!
 */
