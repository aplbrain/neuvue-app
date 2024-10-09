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

import {makeExtraKeyBindings} from 'ngwrapper/extra_key_bindings';
import {navigateToOrigin} from 'ngwrapper/navigate_to_origin';
import {registerActionListener} from 'neuroglancer/util/event_action_map';
import {bindDefaultCopyHandler, bindDefaultPasteHandler} from 'neuroglancer/ui/default_clipboard_handling';
import {setDefaultInputEventBindings} from 'neuroglancer/ui/default_input_event_bindings';

import 'neuroglancer/sliceview/chunk_format_handlers';

import {StatusMessage} from 'neuroglancer/status';
import {DisplayContext} from 'neuroglancer/display_context';
import {Viewer, ViewerOptions} from 'neuroglancer/viewer';
import {disableContextMenu, disableWheel} from 'neuroglancer/ui/disable_default_actions';
function makeDefaultViewer(options?: Partial<ViewerOptions>) {
  disableContextMenu();
  disableWheel();
  try {
    let display = new DisplayContext(document.getElementById('neuroglancer-container')!);
    return new Viewer(display, options);
  } catch (error) {
    StatusMessage.showMessage(`Error: ${error.message}`);
    throw error;
  }
}


window.addEventListener('DOMContentLoaded', () => {

  const viewer = (<any>window)['viewer'] = makeDefaultViewer({showLayerDialog : false});
  setDefaultInputEventBindings(viewer.inputEventBindings);

  viewer.loadFromJsonUrl();
  viewer.initializeSaver();

  bindDefaultCopyHandler(viewer);
  bindDefaultPasteHandler(viewer);

  makeExtraKeyBindings(viewer.inputEventMap);
  registerActionListener(viewer.element, 'navigate-to-origin', () => navigateToOrigin(viewer));
});
