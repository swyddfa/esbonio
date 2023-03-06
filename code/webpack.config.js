//@ts-check

// Originally based on
// https://github.com/microsoft/vscode-extension-samples/blob/cf477847244cf291aa13fa447f1c9cf834f302c8/webpack-sample/webpack.config.js

const path = require('path')

// Configuration for the "main" version of the VSCode extension
/**@type {import('webpack').Configuration}*/
const electronConfig = {
  target: 'node',
  entry: './src/node/extension.ts',
  output: {
    path: path.resolve(__dirname, 'dist', 'node'),
    filename: 'extension.js',
    libraryTarget: 'commonjs2',
    devtoolModuleFilenameTemplate: '../[resource-path]'
  },
  devtool: 'source-map',
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

// Configuration for the "browser" version of the VSCode extension
/**@type {import('webpack').Configuration}*/
const webExtConfig = {
  target: 'webworker',
  entry: './src/browser/extension.ts',
  output: {
    path: path.resolve(__dirname, 'dist', 'browser'),
    filename: 'extension.js',
    libraryTarget: 'commonjs',
  },
  devtool: 'source-map',
  externals: {
    vscode: "commonjs vscode"
  },
  resolve: {
    extensions: ['.ts', '.js'],
    mainFields: ['module', 'main'],
    fallback: {
      path: require.resolve('path-browserify')
    }
  },
  module: {
    rules: [
      {
        test: /.ts$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'ts-loader',
          }
        ]
      }
    ]
  }
}

// Configuration for the language server glue code.
/**@type {import('webpack').Configuration}*/
const lspWorkerConfig = {
  target: 'webworker',
  entry: './src/browser/lsp/worker.ts',
  output: {
    path: path.resolve(__dirname, 'dist', 'browser'),
    filename: 'worker.js',
    libraryTarget: 'var',
    library: 'serverExportVar'
  },
  devtool: 'source-map',
  externals: {
    vscode: "commonjs vscode"
  },
  resolve: {
    extensions: ['.ts', '.js'],
    mainFields: ['module', 'main'],
    fallback: {
      path: require.resolve('path-browserify')
    }
  },
  module: {
    rules: [
      {
        test: /.ts$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'ts-loader',
          }
        ]
      },
      {
        test: /\.py$/,
        type: 'asset/source'
      }
    ]
  }
}

module.exports = [electronConfig, webExtConfig, lspWorkerConfig]
