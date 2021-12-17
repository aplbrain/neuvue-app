/**
 * @license
 * Copyright 2016 Google Inc.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use strict';

const path = require('path');
const webpack_helpers = require('./webpack_helpers');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = env => {
  env = env || 'dev';
  let origConfigs = webpack_helpers.getViewerConfigFromEnv({outputPath: path.resolve(__dirname, '../dist/' + env)}, env);
  let configs = []
  for (const [index, origConfig] of origConfigs.entries()) {

    let origPlugins = origConfig.plugins || []
    
    origPlugins.push(new BundleTracker({filename: `./webpack-stats-${index}.json`}))
    let origOutput = origConfig.output || {}
    let output = Object.assign(
      origOutput,
      {
        filename: '[name].bundle.js',
        chunkFilename: '[name].bundle.js',
      },
    )
    let config = Object.assign(
      origConfig,
      {
        plugins: origPlugins,
        output: output,
      }
    )
    configs.push(config);

  };
  
  return configs;
};
