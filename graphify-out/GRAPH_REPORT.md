# Graph Report - /Users/swapniel/git/agent_curator  (2026-05-05)

## Corpus Check
- 12 files · ~76,554 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 669 nodes · 2099 edges · 69 communities (56 shown, 13 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.93)
- Token cost: 31,627 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]

## God Nodes (most connected - your core abstractions)
1. `getValueByPath()` - 317 edges
2. `setValueByPath()` - 305 edges
3. `isVertexAI()` - 46 edges
4. `request()` - 37 edges
5. `then()` - 35 edges
6. `tModel()` - 33 edges
7. `formatMap()` - 30 edges
8. `get()` - 29 edges
9. `connect()` - 23 edges
10. `tContent()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Basic demo flow sequence` --rationale_for--> `Agentic Loop`  [EXTRACTED]
  CLAUDE.md → extension/sidepanel.js
- `Manifest V3 security & permissions` --references--> `FastMCP CORS middleware`  [INFERRED]
  extension/manifest.json → main.py
- `FastMCP CORS middleware` --rationale_for--> `callMcpTool function`  [INFERRED]
  main.py → extension/sidepanel.js
- `Streamable-HTTP MCP protocol transport` --rationale_for--> `callMcpTool function`  [EXTRACTED]
  main.py → extension/sidepanel.js
- `loadMcpTools function` --references--> `fetch_tech_news MCP Tool`  [EXTRACTED]
  extension/sidepanel.js → main.py

## Hyperedges (group relationships)
- **MCP Tool Ecosystem** — main_fetch_tech_news, main_manage_local_library, main_render_prefab_dashboard [EXTRACTED 1.00]
- **Frontend Agentic Orchestration Flow** — sidepanel_mcpinitialize, sidepanel_loadmcptools, sidepanel_agentic_loop, sidepanel_callmcptool [EXTRACTED 1.00]
- **Data Persistence & Shared Structures** — saved_articles_json_data, last_dashboard_html_cache, main_fetch_tech_news, main_manage_local_library, main_render_prefab_dashboard [EXTRACTED 1.00]

## Communities (69 total, 13 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (57): audioTranscriptionConfigToMldev(), audioTranscriptionConfigToMldev$1(), contentToMldev(), contentToMldev$1(), contentToMldev$2(), contentToMldev$4(), contentToVertex(), contentToVertex$1() (+49 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (48): blobToMldev$1(), cancelTuningJobResponseFromVertex(), candidateFromMldev$1(), citationMetadataFromMldev$1(), computeTokensResponseFromVertex(), countTokensResponseFromMldev(), countTokensResponseFromVertex(), createAuthTokenConfigToMldev() (+40 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (47): batchJobDestinationToVertex(), cancelTuningJobResponseFromMldev(), candidateFromMldev(), citationMetadataFromMldev(), contentEmbeddingFromVertex(), contentEmbeddingStatisticsFromVertex(), controlReferenceConfigToVertex(), deleteCachedContentResponseFromMldev() (+39 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (28): __asyncGenerator(), __asyncValues(), __await(), callTool(), concatBytes(), decode(), decodeUTF8(), encodeUTF8() (+20 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (25): Chrome extension icon click handler, Basic demo flow sequence, Dynamic MCP to Gemini tool binding, Fallback error handling pattern, genai.js bundled ES module, _LAST_DASHBOARD_HTML server cache, GET /dashboard route, fetch_tech_news MCP Tool (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (24): cancel(), cancelBatchJobParametersToMldev(), cancelBatchJobParametersToVertex(), cancelTuningJobParametersToMldev(), cancelTuningJobParametersToVertex(), delete(), deleteBatchJobParametersToMldev(), deleteBatchJobParametersToVertex() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (21): constructor(), crossError(), download(), downloadFile(), fetchUploadUrl(), getBlobStat(), getDefaultFetch(), getFileName() (+13 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (20): listBatchJobsConfigToMldev(), listBatchJobsConfigToVertex(), listBatchJobsParametersToMldev(), listBatchJobsParametersToVertex(), listCachedContentsConfigToMldev(), listCachedContentsConfigToVertex(), listCachedContentsParametersToMldev(), listCachedContentsParametersToVertex() (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.19
Nodes (15): appendGemini(), callMcpTool(), checkServer(), clearGemini(), loadMcpTools(), mcpInitialize(), mcpRequest(), mcpToolsToFunctionDeclarations() (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (19): connect(), getApiKey(), getApiVersion(), getBaseUrl(), getCustomBaseUrl(), getDefaultHeaders(), getHeaders(), getNextGenClient() (+11 more)

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (18): generateVideosConfigToMldev(), generateVideosConfigToVertex(), generateVideosInternal(), generateVideosParametersToMldev(), generateVideosParametersToVertex(), generateVideosSourceToMldev(), generateVideosSourceToVertex(), imageToMldev() (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (17): computeTokens(), computeTokensParametersToVertex(), countTokens(), countTokensConfigToMldev(), countTokensParametersToMldev(), countTokensParametersToVertex(), createFileSearchStoreConfigToMldev(), createFileSearchStoreParametersToMldev() (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (17): create(), get(), getDocumentParametersToMldev(), getFileSearchStoreParametersToMldev(), isMcpClient(), list(), mcpToTool(), methodRequest() (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (15): addAuthHeaders(), asResponse(), authHeaders(), calculateDefaultRetryTimeoutMillis(), finally(), getAuthHeaders(), getHeadersInternal(), handleWebSocketMessage() (+7 more)

### Community 15 - "Community 15"
Cohesion: 0.16
Nodes (14): baseURLOverridden(), buildBody(), buildHeaders(), buildRequest(), buildURL(), defaultIdempotencyKey(), defaultQuery(), getUserAgent() (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (13): CancelReadableStream(), defaultParseResponse(), fetchWithTimeout(), fromSSEResponse(), generate(), isAbortError(), loggerFor(), _makeAbort() (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (10): dashboard(), fetch_tech_news(), _load_library(), manage_local_library(), Read/write the local saved_articles.json library.      action='check_duplicates', Compile curated articles and data into a professional dashboard.      Each card:, Serve last rendered Prefab dashboard HTML with theme support., Primary tool for DEVELOPER TRENDS and COMMUNITY DISCUSSION.     Use this for: "W (+2 more)

### Community 18 - "Community 18"
Cohesion: 0.22
Nodes (11): createTuningJobParametersPrivateToVertex(), downloadMedia(), fetchPredictOperationParametersToVertex(), fetchPredictVideosOperationInternal(), getOperationParametersToMldev(), getOperationParametersToVertex(), getVideosOperation(), getVideosOperationInternal() (+3 more)

### Community 19 - "Community 19"
Cohesion: 0.18
Nodes (11): createFileParametersToMldev(), createInternal(), embedContentInternal(), formatMap(), getInternal(), getTuningJobParametersToMldev(), getTuningJobParametersToVertex(), internalRegisterFilesParametersToMldev() (+3 more)

### Community 20 - "Community 20"
Cohesion: 0.22
Nodes (9): batchJobSourceToMldev(), batchJobSourceToVertex(), createBatchJobConfigToMldev(), createBatchJobConfigToVertex(), createBatchJobParametersToMldev(), createBatchJobParametersToVertex(), createInlinedGenerateContentRequest(), tBatchJobDestination() (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (9): _fromAPIResponse(), generateVideosOperationFromMldev$1(), generateVideosOperationFromVertex$1(), generateVideosResponseFromMldev$1(), generateVideosResponseFromVertex$1(), importFileOperationFromMldev$1(), importFileResponseFromMldev$1(), uploadToFileSearchStoreOperationFromMldev() (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.28
Nodes (9): constructUrl(), getBaseResourcePath(), patchHttpOptions(), request(), requestStream(), shouldPrependVertexProjectPath(), uploadToFileSearchStoreConfigToMldev(), uploadToFileSearchStoreInternal() (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.31
Nodes (9): apiCall(), catch(), importFile(), importFileConfigToMldev(), importFileParametersToMldev(), sendMessageStream(), streamApiCall(), then() (+1 more)

### Community 24 - "Community 24"
Cohesion: 0.29
Nodes (8): batchJobDestinationFromMldev(), batchJobDestinationFromVertex(), batchJobFromMldev(), batchJobFromVertex(), batchJobSourceFromVertex(), tJobState(), tRecvBatchJobDestination(), vertexMultimodalDatasetDestinationFromVertex()

### Community 25 - "Community 25"
Cohesion: 0.52
Nodes (7): liveSendRealtimeInputParametersToMldev(), liveSendRealtimeInputParametersToVertex(), sendRealtimeInput(), tAudioBlob(), tBlob(), tBlobs(), tImageBlob()

### Community 26 - "Community 26"
Cohesion: 0.33
Nodes (6): initAfcToolsMap(), isCallableTool(), mcpToGeminiTool(), mcpToolsToGeminiTool(), shouldDisableAfc(), tool()

### Community 27 - "Community 27"
Cohesion: 0.47
Nodes (6): createCachedContentParametersToVertex(), getLocation(), getProject(), prepareOptions(), resourceName(), tCachesModel()

### Community 28 - "Community 28"
Cohesion: 0.4
Nodes (5): contentToMldev$3(), createCachedContentConfigToMldev(), createCachedContentParametersToMldev(), functionCallingConfigToMldev$1(), toolConfigToMldev$1()

### Community 29 - "Community 29"
Cohesion: 0.4
Nodes (5): generatedVideoFromMldev$1(), generatedVideoFromVertex$1(), tBytes$1(), videoFromMldev$1(), videoFromVertex$1()

### Community 30 - "Community 30"
Cohesion: 0.4
Nodes (5): generatedImageFromVertex(), generatedImageMaskFromVertex(), generateImagesResponseFromVertex(), imageFromVertex(), safetyAttributesFromVertex()

### Community 31 - "Community 31"
Cohesion: 0.4
Nodes (5): createModelContent(), createPartFromText(), createUserContent(), _isPart(), _toParts()

### Community 32 - "Community 32"
Cohesion: 0.4
Nodes (5): getBytes(), getName(), makeFile(), propsForError(), toFile()

### Community 33 - "Community 33"
Cohesion: 0.4
Nodes (5): pause(), play(), resetContext(), sendPlaybackControl(), stop()

### Community 34 - "Community 34"
Cohesion: 0.5
Nodes (4): authConfigToMldev$4(), googleMapsToMldev$4(), googleSearchToMldev$4(), toolToMldev$4()

### Community 35 - "Community 35"
Cohesion: 0.5
Nodes (4): authConfigToMldev$1(), googleMapsToMldev$1(), googleSearchToMldev$1(), toolToMldev$1()

### Community 36 - "Community 36"
Cohesion: 0.5
Nodes (4): blobToMldev$2(), fileDataToMldev$2(), functionCallToMldev$2(), partToMldev$2()

### Community 37 - "Community 37"
Cohesion: 0.5
Nodes (4): blobToMldev$4(), fileDataToMldev$4(), functionCallToMldev$4(), partToMldev$4()

### Community 38 - "Community 38"
Cohesion: 0.5
Nodes (4): authConfigToMldev$2(), googleMapsToMldev$2(), googleSearchToMldev$2(), toolToMldev$2()

### Community 39 - "Community 39"
Cohesion: 0.5
Nodes (4): blobToMldev(), fileDataToMldev(), functionCallToMldev(), partToMldev()

### Community 40 - "Community 40"
Cohesion: 0.5
Nodes (4): generatedImageFromMldev(), generateImagesResponseFromMldev(), imageFromMldev(), safetyAttributesFromMldev()

### Community 41 - "Community 41"
Cohesion: 0.5
Nodes (4): authConfigToMldev(), googleMapsToMldev(), googleSearchToMldev(), toolToMldev()

### Community 42 - "Community 42"
Cohesion: 0.5
Nodes (4): blobToMldev$3(), fileDataToMldev$3(), functionCallToMldev$3(), partToMldev$3()

### Community 43 - "Community 43"
Cohesion: 0.5
Nodes (4): authConfigToMldev$3(), googleMapsToMldev$3(), googleSearchToMldev$3(), toolToMldev$3()

### Community 44 - "Community 44"
Cohesion: 0.5
Nodes (4): tTuningJobStatus(), tunedModelFromMldev(), tuningJobFromMldev(), tuningJobFromVertex()

### Community 45 - "Community 45"
Cohesion: 0.5
Nodes (4): recontextImage(), recontextImageConfigToVertex(), recontextImageParametersToVertex(), recontextImageSourceToVertex()

### Community 46 - "Community 46"
Cohesion: 0.5
Nodes (4): createEmbeddingsBatchJobConfigToMldev(), createEmbeddingsBatchJobParametersToMldev(), createEmbeddingsInternal(), embeddingsBatchJobSourceToMldev()

### Community 47 - "Community 47"
Cohesion: 0.5
Nodes (4): createTuningJobConfigToMldev(), createTuningJobParametersPrivateToMldev(), tuneMldevInternal(), tuningDatasetToMldev()

### Community 48 - "Community 48"
Cohesion: 0.5
Nodes (4): hasNextPage(), init(), initNextPage(), nextPage()

### Community 49 - "Community 49"
Cohesion: 0.5
Nodes (4): hasField(), listModelsResponseFromMldev(), listModelsResponseFromVertex(), tExtractModels()

### Community 50 - "Community 50"
Cohesion: 0.67
Nodes (3): upscaleImageAPIConfigInternalToVertex(), upscaleImageAPIParametersInternalToVertex(), upscaleImageInternal()

### Community 51 - "Community 51"
Cohesion: 0.67
Nodes (3): editImageConfigToVertex(), editImageInternal(), editImageParametersInternalToVertex()

### Community 52 - "Community 52"
Cohesion: 0.67
Nodes (3): formatDestination(), getBigqueryUri(), getGcsUri()

## Knowledge Gaps
- **17 isolated node(s):** `Primary tool for DEVELOPER TRENDS and COMMUNITY DISCUSSION.     Use this for: "W`, `Read/write the local saved_articles.json library.      action='check_duplicates'`, `Compile curated articles and data into a professional dashboard.      Each card:`, `Serve last rendered Prefab dashboard HTML with theme support.`, `Theme toggle UI` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `getValueByPath()` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 6`, `Community 8`, `Community 11`, `Community 12`, `Community 13`, `Community 18`, `Community 19`, `Community 20`, `Community 21`, `Community 22`, `Community 23`, `Community 24`, `Community 25`, `Community 27`, `Community 28`, `Community 29`, `Community 30`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 46`, `Community 47`, `Community 49`, `Community 50`, `Community 51`, `Community 54`, `Community 55`, `Community 56`, `Community 57`, `Community 59`, `Community 62`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `setValueByPath()` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 8`, `Community 11`, `Community 12`, `Community 13`, `Community 18`, `Community 19`, `Community 20`, `Community 21`, `Community 22`, `Community 23`, `Community 24`, `Community 25`, `Community 27`, `Community 28`, `Community 29`, `Community 30`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 46`, `Community 47`, `Community 49`, `Community 50`, `Community 51`, `Community 54`, `Community 55`, `Community 56`, `Community 57`, `Community 59`, `Community 62`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `isVertexAI()` connect `Community 18` to `Community 0`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 14`, `Community 19`, `Community 20`, `Community 22`, `Community 23`, `Community 25`, `Community 27`, `Community 45`, `Community 46`, `Community 47`, `Community 50`, `Community 51`, `Community 61`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **What connects `Primary tool for DEVELOPER TRENDS and COMMUNITY DISCUSSION.     Use this for: "W`, `Read/write the local saved_articles.json library.      action='check_duplicates'`, `Compile curated articles and data into a professional dashboard.      Each card:` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._