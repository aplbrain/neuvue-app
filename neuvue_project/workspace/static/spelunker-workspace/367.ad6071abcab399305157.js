const A=367,T=[367],C={2366:(E,h,l)=>{l.d(h,{R:()=>u});var o=l(4509),s=l(9808);/**
 * @license
 * Copyright 2019 Google Inc.
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
 */const r=3;async function u(n,i,f,e,t,a,m=o.fx){let _;for(let R=0;;){(0,o.Dq)(m),R>1&&await new Promise(p=>setTimeout(p,(0,s.JZ)(R-2))),_=await n.get(_,m);try{return await(0,s.Bk)(typeof i=="function"?i(_.credentials):i,t(_.credentials,f),e,m)}catch(p){if(p instanceof s.j$&&await a(p,_.credentials)==="refresh"){if(++R===r)throw p;continue}throw p}}}},3551:(E,h,l)=>{l.d(h,{Y:()=>u});var o=l(2366),s=l(4509),r=l(9808);/**
 * @license
 * Copyright 2020 Google Inc.
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
 */function u(n,i,f,e,t=s.fx){return n===void 0?(0,r.Bk)(i,f,e,t):(0,o.R)(n,i,f,e,(a,m)=>{if(!a.accessToken)return m;const _=new Headers(m.headers);return _.set("Authorization",`${a.tokenType} ${a.accessToken}`),{...m,headers:_}},n.errorHandler,t)}},957:(E,h,l)=>{l.d(h,{P:()=>o,y:()=>s});/**
 * @license
 * Copyright 2017 Google Inc.
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
 */const o="CredentialsProvider",s="CredentialsProvider.get"},6650:(E,h,l)=>{l.d(h,{Ve:()=>r,jj:()=>s});/**
 * @license
 * Copyright 2017 Google Inc.
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
 */class o{}class s extends o{static stringify(n){return`boss:volume:${n.baseUrl}/${n.collection}/${n.experiment}/${n.channel}/${n.resolution}/${n.encoding}`}}s.RPC_ID="boss/VolumeChunkSource";class r{static stringify(n){return`boss:mesh:${n.baseUrl}`}}r.RPC_ID="boss/MeshChunkSource"},2020:(E,h,l)=>{l.d(h,{CR:()=>r,Ip:()=>u,NV:()=>i,Rw:()=>e,Ve:()=>n,r7:()=>o,rl:()=>f});/**
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
 */var o=(t=>(t[t.RAW=0]="RAW",t[t.JPEG=1]="JPEG",t[t.COMPRESSED_SEGMENTATION=2]="COMPRESSED_SEGMENTATION",t))(o||{});class s{}class r{}r.RPC_ID="brainmaps/VolumeChunkSource";class u{}u.RPC_ID="brainmaps/MultiscaleMeshSource";class n{}n.RPC_ID="brainmaps/MeshSource";class i{}i.RPC_ID="brainmaps/SkeletonSource";class f{}f.RPC_ID="brainmaps/Annotation";class e{}e.RPC_ID="brainmaps/AnnotationSpatialIndex"},5990:(E,h,l)=>{l.d(h,{D:()=>s,j:()=>o});/**
 * @license
 * Copyright 2016 Google Inc., 2023 Gergely Csucs
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
 */var o=(r=>(r[r.JPG=0]="JPG",r[r.JPEG=1]="JPEG",r[r.PNG=2]="PNG",r))(o||{});class s{}s.RPC_ID="deepzoom/ImageTileSource"},8820:(E,h,l)=>{l.d(h,{NV:()=>u,Ve:()=>n,jj:()=>r,r7:()=>o});/**
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
 */var o=(i=>(i[i.JPEG=0]="JPEG",i[i.RAW=1]="RAW",i[i.COMPRESSED_SEGMENTATION=2]="COMPRESSED_SEGMENTATION",i[i.COMPRESSED_SEGMENTATIONARRAY=3]="COMPRESSED_SEGMENTATIONARRAY",i))(o||{});class s{}class r extends s{}r.RPC_ID="dvid/VolumeChunkSource";class u extends s{}u.RPC_ID="dvid/SkeletonSource";class n extends s{}n.RPC_ID="dvid/MeshSource"},5926:(E,h,l)=>{l.d(h,{j:()=>s,r:()=>o});/**
 * @license
 * Copyright 2019 Google Inc.
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
 */var o=(r=>(r[r.RAW=0]="RAW",r[r.GZIP=1]="GZIP",r[r.BLOSC=2]="BLOSC",r[r.ZSTD=3]="ZSTD",r))(o||{});class s{}s.RPC_ID="n5/VolumeChunkSource"},6435:(E,h,l)=>{l.d(h,{C:()=>s,Y:()=>o});/**
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
 */const o="nifti/getNiftiVolumeInfo";class s{}s.RPC_ID="nifti/VolumeChunkSource"},3819:(E,h,l)=>{l.d(h,{Ip:()=>f,NV:()=>e,Rw:()=>t,TV:()=>n,Ve:()=>r,Y1:()=>u,jj:()=>s,r7:()=>o,rl:()=>a,vq:()=>m});/**
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
 */var o=(_=>(_[_.RAW=0]="RAW",_[_.JPEG=1]="JPEG",_[_.COMPRESSED_SEGMENTATION=2]="COMPRESSED_SEGMENTATION",_[_.COMPRESSO=3]="COMPRESSO",_[_.PNG=4]="PNG",_))(o||{});class s{}s.RPC_ID="precomputed/VolumeChunkSource";class r{}r.RPC_ID="precomputed/MeshSource";var u=(_=>(_[_.RAW=0]="RAW",_[_.GZIP=1]="GZIP",_))(u||{}),n=(_=>(_[_.IDENTITY=0]="IDENTITY",_[_.MURMURHASH3_X86_128=1]="MURMURHASH3_X86_128",_))(n||{});class i{}class f{}f.RPC_ID="precomputed/MultiscaleMeshSource";class e{}e.RPC_ID="precomputed/SkeletonSource";class t{}t.RPC_ID="precomputed/AnnotationSpatialIndexSource";class a{}a.RPC_ID="precomputed/AnnotationSource";class m{}m.RPC_ID="precomputed/IndexedSegmentPropertySource"},8997:(E,h,l)=>{l.d(h,{vc:()=>r});/**
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
 */class o{}class s extends o{}class r extends s{}r.RPC_ID="render/TileChunkSource"},6742:(E,h,l)=>{l.d(h,{j:()=>o});/**
 * @license
 * Copyright 2019 Google Inc.
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
 */class o{}o.RPC_ID="zarr/VolumeChunkSource"},2334:(E,h,l)=>{l.d(h,{L:()=>o});/**
 * @license
 * Copyright 2023 Google Inc.
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
 */var o=(s=>(s[s.arrayToArray=0]="arrayToArray",s[s.arrayToBytes=1]="arrayToBytes",s[s.bytesToBytes=2]="bytesToBytes",s))(o||{})},9254:(E,h,l)=>{l.d(h,{_:()=>r});/**
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
 */const o=3432918353,s=461845907;function r(u,n){return n>>>=0,u>>>=0,n=Math.imul(n,o)>>>0,n=(n<<15|n>>>17)>>>0,n=Math.imul(n,s)>>>0,u=(u^n)>>>0,u=(u<<13|u>>>19)>>>0,u=u*5+3864292196>>>0,u}},3708:(E,h,l)=>{l.d(h,{Of:()=>o,Pc:()=>n,Yo:()=>s,dI:()=>r,pi:()=>u});/**
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
 */const o="mesh/MeshLayer",s="mesh/MultiscaleMeshLayer",r="mesh/FragmentSource",u="mesh/MultiscaleFragmentSource";var n=(i=>(i[i.float32=0]="float32",i[i.uint10=1]="uint10",i[i.uint16=2]="uint16",i))(n||{})},4373:(E,h,l)=>{l.d(h,{l:()=>o});/**
 * @license
 * Copyright 2018 Google Inc.
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
 */const o="perspective_view/PerspectiveView"},3517:(E,h,l)=>{l.d(h,{Bh:()=>r,kg:()=>u,lG:()=>s,sC:()=>o});/**
 * @license
 * Copyright 2019 Google Inc.
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
 */const o="rendered_view.addLayer",s="rendered_view.removeLayer",r="SharedProjectionParameters",u="SharedProjectionParameters.changed"},6015:(E,h,l)=>{l.d(h,{Fe:()=>n,N3:()=>s,b7:()=>r,nG:()=>o});/**
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
 */const o="single_mesh/SingleMeshLayer",s="single_mesh/getSingleMeshInfo",r="";class u{}class n extends u{}n.RPC_ID="single_mesh/SingleMeshSource"},3786:(E,h,l)=>{l.d(h,{k:()=>o});/**
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
 */const o="skeleton/SkeletonLayer"},9459:(E,h,l)=>{l.d(h,{i:()=>r});var o=l(3038),s=l(147);/**
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
 */class r{constructor(n,i,f){this.size=o.eR.clone(n),this.transform=o.pB.clone(i),this.finiteRank=f;const e=o.pB.create(),t=s.DI(e,4,i,4,4);if(t===0)throw new Error("Transform is singular");this.invTransform=e,this.detTransform=t}toObject(){return{size:this.size,transform:this.transform,finiteRank:this.finiteRank}}static fromObject(n){return new r(n.size,n.transform,n.finiteRank)}globalToLocalSpatial(n,i){return o.eR.transformMat4(n,i,this.invTransform)}localSpatialVectorToGlobal(n,i){return(0,o.vs)(n,i,this.transform)}globalToLocalNormal(n,i){return(0,o.uD)(n,i,this.transform)}}},4104:(E,h,l)=>{l.d(h,{t:()=>o});/**
 * @license
 * Copyright 2017 Google Inc.
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
 */function o(s){let r=-1;return Object.assign(()=>{r===-1&&(r=requestAnimationFrame(()=>{r=-1,s()}))},{flush:()=>{r!==-1&&(r=-1,s())},cancel:()=>{r!==-1&&(cancelAnimationFrame(r),r=-1)}})}},9100:(E,h,l)=>{l.d(h,{I:()=>w});var o=l(4242),s=l(3206),r=l(8796);/**
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
 */const u=Symbol("disjoint_sets:rank"),n=Symbol("disjoint_sets:parent"),i=Symbol("disjoint_sets:next"),f=Symbol("disjoint_sets:prev");function e(P){let c=P,S=P[n];for(;S!==P;)P=S,S=P[n];for(P=c[n];S!==P;)c[n]=S,c=P,P=c[n];return S}function t(P,c){const S=P[u],d=c[u];return S>d?(c[n]=P,P):(P[n]=c,S===d&&(c[u]=d+1),c)}function a(P,c){const S=P[f],d=c[f];c[f]=S,S[i]=c,P[f]=d,d[i]=P}function*m(P){let c=P;do yield c,c=c[i];while(c!==P)}function _(P){P[n]=P,P[u]=0,P[i]=P[f]=P}const R=Symbol("disjoint_sets:min");function p(P){return P[n]===P}class w{constructor(){this.map=new Map,this.visibleSegmentEquivalencePolicy=new s.B0(o.y6.MIN_REPRESENTATIVE),this.generation=0}has(c){const S=c.toString();return this.map.get(S)!==void 0}get(c){const S=c.toString(),d=this.map.get(S);return d===void 0?c:e(d)[R]}isMinElement(c){const S=this.get(c);return S===c||r.R.equal(S,c)}makeSet(c){const S=c.toString(),{map:d}=this;let g=d.get(S);return g===void 0?(g=c.clone(),_(g),g[R]=g,d.set(S,g),g):e(g)}link(c,S){if(c=this.makeSet(c),S=this.makeSet(S),c===S)return!1;this.generation++;const d=t(c,S);a(c,S);const g=c[R],I=S[R],D=(this.visibleSegmentEquivalencePolicy.value&o.y6.MAX_REPRESENTATIVE)!==0;return d[R]=r.R.less(g,I)===D?I:g,!0}linkAll(c){for(let S=1,d=c.length;S<d;++S)this.link(c[0],c[S])}deleteSet(c){const{map:S}=this;let d=!1;for(const g of this.setElements(c))S.delete(g.toString()),d=!0;return d&&++this.generation,d}*setElements(c){const S=c.toString(),d=this.map.get(S);d===void 0?yield c:yield*m(d)}clear(){const{map:c}=this;return c.size===0?!1:(++this.generation,c.clear(),!0)}get size(){return this.map.size}*mappings(c=new Array(2)){for(const S of this.map.values())c[0]=S,c[1]=e(S)[R],yield c}*roots(){for(const c of this.map.values())p(c)&&(yield c)}[Symbol.iterator](){return this.mappings()}toJSON(){const c=new Array;for(const S of this.map.values())if(p(S)){const d=new Array;for(const g of m(S))d.push(g);d.sort(r.R.compare),c.push(d)}return c.sort((S,d)=>r.R.compare(S[0],d[0])),c.map(S=>S.map(d=>d.toString()))}}},8103:(E,h,l)=>{l.d(h,{K:()=>s});/**
 * @license
 * Copyright 2018 Google Inc.
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
 */const o=new Float32Array(1);function s(r){o[0]=r,r=o[0];for(let u=1;u<21;++u){const n=r.toPrecision(u);if(o[0]=parseFloat(n),o[0]===r)return n}return r.toString()}},4472:(E,h,l)=>{l.d(h,{A:()=>o});/**
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
 */const o=class{static insertAfter(s,r){const u=s.next0;r.next0=u,r.prev0=s,s.next0=r,u.prev0=r}static insertBefore(s,r){const u=s.prev0;r.prev0=u,r.next0=s,s.prev0=r,u.next0=r}static front(s){const r=s.next0;return r===s?null:r}static back(s){const r=s.prev0;return r===s?null:r}static pop(s){const r=s.next0,u=s.prev0;return r.prev0=u,u.next0=r,s.next0=null,s.prev0=null,s}static*iterator(s){for(let r=s.next0;r!==s;r=r.next0)yield r}static*reverseIterator(s){for(let r=s.prev0;r!==s;r=r.prev0)yield r}static initializeHead(s){s.next0=s.prev0=s}}},4704:(E,h,l)=>{l.d(h,{d:()=>r,e:()=>u});var o=l(2596),s=l(7900);/**
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
 */class r{constructor(){this.map=new Map}get(i,f){const{map:e}=this;let t=e.get(i);return t===void 0?(t=f(),t.registerDisposer(()=>{e.delete(i)}),e.set(i,t)):t.addRef(),t}}class u extends r{get(i,f){return typeof i!="string"&&(i=(0,s.JB)(i)),super.get(i,f)}getUncounted(i,f){return this.get(i,()=>new o.fL(f())).value}}},8795:(E,h,l)=>{l.d(h,{e:()=>o});/**
 * @license
 * Copyright 2019 Google Inc.
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
 */function o(s,r){return s<r?-1:s>r?1:0}},6703:(E,h,l)=>{l.d(h,{F:()=>r});var o=l(7900),s=l(4038);/**
 * @license
 * Copyright 2017 Google Inc.
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
 */class r{constructor(n,i,f=i){this.enumType=n,this.value_=i,this.defaultValue=f,this.changed=new s.IY}set value(n){this.value_!==n&&(this.value_=n,this.changed.dispatch())}get value(){return this.value_}reset(){this.value=this.defaultValue}restoreState(n){this.value=(0,o.sl)(n,this.enumType)}toJSON(){if(this.value_!==this.defaultValue)return this.enumType[this.value_].toLowerCase()}}},8796:(E,h,l)=>{l.d(h,{R:()=>i});/**
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
 */const o=new Uint32Array(2),s=4294967296,r=[];for(let f=2;f<=36;++f){const e=Math.floor(32/Math.log2(f)),t=f**e;let a=`^[0-${String.fromCharCode(48+Math.min(9,f-1))}`;f>10&&(a+=`a-${String.fromCharCode(97+f-11)}`,a+=`A-${String.fromCharCode(65+f-11)}`);const m=Math.ceil(64/Math.log2(f));a+=`]{1,${m}}$`;const _=new RegExp(a);r[f]={lowDigits:e,lowBase:t,pattern:_}}function u(f,e){f>>>=0,e>>>=0;const t=f&65535,a=f>>>16,m=e&65535,_=e>>>16;let p=(t*m>>>16)+a*m,w=p>>>16;p=(p&65535)+t*_,w+=p>>>16;let P=w>>>16;return w=(w&65535)+a*_,P+=w>>>16,((P&65535)<<16|w&65535)>>>0}const n=class M{constructor(e=0,t=0){this.low=e,this.high=t}clone(){return new M(this.low,this.high)}assign(e){this.low=e.low,this.high=e.high}toString(e=10){let t=this.low,a=this.high;if(a===0)return t.toString(e);a*=s;const{lowBase:m,lowDigits:_}=r[e],R=a%m;a=Number(BigInt(a)/BigInt(m)),t+=R,a+=Math.floor(t/m),t=t%m;const p=t.toString(e);return a.toString(e)+"0".repeat(_-p.length)+p}static less(e,t){return e.high<t.high||e.high===t.high&&e.low<t.low}static compare(e,t){return e.high-t.high||e.low-t.low}static equal(e,t){return e.low===t.low&&e.high===t.high}static min(e,t){return M.less(e,t)?e:t}static max(e,t){return M.less(e,t)?t:e}static random(){return crypto.getRandomValues(o),new M(o[0],o[1])}tryParseString(e,t=10){const{lowDigits:a,lowBase:m,pattern:_}=r[t];if(!_.test(e))return!1;if(e.length<=a)return this.low=parseInt(e,t),this.high=0,!0;const R=e.length-a,p=parseInt(e.substr(R),t),w=parseInt(e.substr(0,R),t);let P,c;if(m===s)P=w,c=p;else{const S=Math.imul(w,m)>>>0;P=u(w,m)+(Math.imul(Math.floor(w/s),m)>>>0),c=p+S,c>=s&&(++P,c-=s)}return c>>>0!==c||P>>>0!==P?!1:(this.low=c,this.high=P,!0)}parseString(e,t=10){if(!this.tryParseString(e,t))throw new Error(`Failed to parse string as uint64 value: ${JSON.stringify(e)}.`);return this}static parseString(e,t=10){return new M().parseString(e,t)}valid(){const{low:e,high:t}=this;return e>>>0===e&&t>>>0===t}toJSON(){return this.toString()}static lshift(e,t,a){const{low:m,high:_}=t;return a===0?(e.low=m,e.high=_):a<32?(e.low=m<<a,e.high=_<<a|m>>>32-a):(e.low=0,e.high=m<<a-32),e}static rshift(e,t,a){const{low:m,high:_}=t;return a===0?(e.low=m,e.high=_):a<32?(e.low=m>>>a|_<<32-a,e.high=_>>>a):(e.low=_>>>a-32,e.high=0),e}static or(e,t,a){return e.low=t.low|a.low,e.high=t.high|a.high,e}static xor(e,t,a){return e.low=t.low^a.low,e.high=t.high^a.high,e}static and(e,t,a){return e.low=t.low&a.low,e.high=t.high&a.high,e}static add(e,t,a){const m=t.low+a.low;let _=t.high+a.high;const R=m>>>0;return R!==m&&(_+=1),e.low=R,e.high=_>>>0,e}static addUint32(e,t,a){const m=t.low+a;let _=t.high;const R=m>>>0;return R!==m&&(_+=1),e.low=R,e.high=_>>>0,e}static decrement(e,t){let{low:a,high:m}=t;return a===0&&(m-=1),e.low=a-1>>>0,e.high=m>>>0,e}static increment(e,t){let{low:a,high:m}=t;return a===4294967295&&(m+=1),e.low=a+1>>>0,e.high=m>>>0,e}static subtract(e,t,a){const m=t.low-a.low;let _=t.high-a.high;const R=m>>>0;return R!==m&&(_-=1),e.low=R,e.high=_>>>0,e}static absDifference(e,t,a){return M.less(t,a)?M.subtract(e,a,t):M.subtract(e,t,a)}static multiplyUint32(e,t,a){const{low:m,high:_}=t;return e.low=Math.imul(m,a)>>>0,e.high=Math.imul(_,a)+u(m,a)>>>0,e}static lowMask(e,t){return t===0?e.high=e.low=0:t<=32?(e.high=0,e.low=4294967295>>>32-t):(e.high=4294967295>>>t-32,e.low=4294967295),e}toNumber(){return this.low+this.high*4294967296}setFromNumber(e){e=Math.round(e),e<0?this.low=this.high=0:e>=18446744073709552e3?this.low=this.high=4294967295:(this.low=e%4294967296,this.high=Math.floor(e/4294967296))}static fromNumber(e){const t=new M;return t.setFromNumber(e),t}};n.ZERO=new n(0,0),n.ONE=new n(1,0);let i=n},310:(E,h,l)=>{l.d(h,{y:()=>r});var o=l(4704);/**
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
 */const s=!1;function r(u){const n={antialias:!1,stencil:!0};s&&(console.log("DEBUGGING via preserveDrawingBuffer"),n.preserveDrawingBuffer=!0);const i=u.getContext("webgl2",n);if(i==null)throw new Error("WebGL not supported.");i.memoize=new o.d,i.maxTextureSize=i.getParameter(i.MAX_TEXTURE_SIZE),i.max3dTextureSize=i.getParameter(i.MAX_3D_TEXTURE_SIZE),i.maxTextureImageUnits=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),i.tempTextureUnit=i.maxTextureImageUnits-1;for(const f of["EXT_color_buffer_float"])if(!i.getExtension(f))throw new Error(`${f} extension not available`);for(const f of["EXT_float_blend"])i.getExtension(f);return i}}};export{A as id,T as ids,C as modules};

//# sourceMappingURL=367.ad6071abcab399305157.js.map