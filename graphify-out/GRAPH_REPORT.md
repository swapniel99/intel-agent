# Graph Report - .  (2026-05-06)

## Corpus Check
- 15 files · ~96,593 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 803 nodes · 2991 edges · 51 communities (47 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.9)
- Token cost: 12,500 input · 2,800 output

## Community Hubs (Navigation)
- [[_COMMUNITY_MCP Server Testing|MCP Server Testing]]
- [[_COMMUNITY_GenAI SDK Internal Logic|GenAI SDK Internal Logic]]
- [[_COMMUNITY_MLDev & Vertex Response Mapping|MLDev & Vertex Response Mapping]]
- [[_COMMUNITY_IntelAgent Core Components|IntelAgent Core Components]]
- [[_COMMUNITY_Vertex AI Job Management|Vertex AI Job Management]]
- [[_COMMUNITY_Part & Content Factory|Part & Content Factory]]
- [[_COMMUNITY_MLDev Configuration Transformers|MLDev Configuration Transformers]]
- [[_COMMUNITY_Agent Curator Backend Handlers|Agent Curator Backend Handlers]]
- [[_COMMUNITY_SDK Auth & Metadata Handling|SDK Auth & Metadata Handling]]
- [[_COMMUNITY_HTTP Request & Retry Logic|HTTP Request & Retry Logic]]
- [[_COMMUNITY_Streaming & SSE Processing|Streaming & SSE Processing]]
- [[_COMMUNITY_Extension Sidepanel Controller|Extension Sidepanel Controller]]
- [[_COMMUNITY_Extension Dashboard Interface|Extension Dashboard Interface]]
- [[_COMMUNITY_URL & Header Builders|URL & Header Builders]]
- [[_COMMUNITY_Live Connectivity & Transcription|Live Connectivity & Transcription]]
- [[_COMMUNITY_File Upload & Blob Management|File Upload & Blob Management]]
- [[_COMMUNITY_REST API Method Proxies|REST API Method Proxies]]
- [[_COMMUNITY_Image & Video Generation (MLDev)|Image & Video Generation (MLDev)]]
- [[_COMMUNITY_Multimodal Processing (Vertex)|Multimodal Processing (Vertex)]]
- [[_COMMUNITY_Tuning & Dataset Management|Tuning & Dataset Management]]
- [[_COMMUNITY_Import & Batch Processing|Import & Batch Processing]]
- [[_COMMUNITY_Predict & Operations API|Predict & Operations API]]
- [[_COMMUNITY_Token & Content Generation|Token & Content Generation]]
- [[_COMMUNITY_Job Cancellation & Deletion|Job Cancellation & Deletion]]
- [[_COMMUNITY_Media Download & SDK Helpers|Media Download & SDK Helpers]]
- [[_COMMUNITY_Low-level Request Routing|Low-level Request Routing]]
- [[_COMMUNITY_Batch Job Configuration|Batch Job Configuration]]
- [[_COMMUNITY_Job State & History|Job State & History]]
- [[_COMMUNITY_Chat History & Messaging|Chat History & Messaging]]
- [[_COMMUNITY_Real-time Input & Audio|Real-time Input & Audio]]
- [[_COMMUNITY_Video Ops (MLDev)|Video Ops (MLDev)]]
- [[_COMMUNITY_Image Ops (Vertex)|Image Ops (Vertex)]]
- [[_COMMUNITY_File System Helpers|File System Helpers]]
- [[_COMMUNITY_Embeddings Batch Jobs|Embeddings Batch Jobs]]
- [[_COMMUNITY_Recontextualization Ops|Recontextualization Ops]]
- [[_COMMUNITY_MLDev Request Fragmenting|MLDev Request Fragmenting]]
- [[_COMMUNITY_MLDev Request Partials|MLDev Request Partials]]
- [[_COMMUNITY_Auth & Google Search Tools|Auth & Google Search Tools]]
- [[_COMMUNITY_Tool Integration (MLDev)|Tool Integration (MLDev)]]
- [[_COMMUNITY_Tool Call Metadata|Tool Call Metadata]]
- [[_COMMUNITY_Function Call Fragmenting|Function Call Fragmenting]]
- [[_COMMUNITY_Search & Maps Tooling|Search & Maps Tooling]]
- [[_COMMUNITY_External Tool Providers|External Tool Providers]]
- [[_COMMUNITY_Image Generation Logic|Image Generation Logic]]
- [[_COMMUNITY_Options UI Form|Options UI Form]]
- [[_COMMUNITY_PRD Specification|PRD Specification]]
- [[_COMMUNITY_Architecture Documentation|Architecture Documentation]]
- [[_COMMUNITY_Claude Architecture Guide|Claude Architecture Guide]]

## God Nodes (most connected - your core abstractions)
1. `getValueByPath()` - 318 edges
2. `setValueByPath()` - 306 edges
3. `isVertexAI()` - 47 edges
4. `request()` - 38 edges
5. `then()` - 36 edges
6. `tModel()` - 34 edges
7. `formatMap()` - 31 edges
8. `get()` - 30 edges
9. `_parse()` - 25 edges
10. `_call()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `options.js Settings Page Script` --semantically_similar_to--> `saved_articles.json Local Library`  [AMBIGUOUS] [semantically similar]
  extension/options.js → saved_articles.json
- `Fallback to saved_articles.json on network failure` --references--> `saved_articles.json Local Library`  [INFERRED]
  main.py → saved_articles.json
- `dashboard GET Route` --rationale_for--> `Dashboard iframe Rendering Pattern`  [EXTRACTED]
  main.py → extension/sidepanel.html
- `Agentic Loop` --rationale_for--> `Basic demo flow sequence`  [EXTRACTED]
  extension/sidepanel.js → CLAUDE.md
- `Manifest V3 security & permissions` --references--> `FastMCP CORS middleware`  [INFERRED]
  extension/manifest.json → main.py

## Communities (51 total, 4 thin omitted)

### Community 0 - "MCP Server Testing"
Cohesion: 0.1
Nodes (55): _call(), _parse(), MCP server integration tests. Requires server running at http://localhost:8000., test_dashboard_route_dark(), test_dashboard_route_light(), test_fetch_all_sources(), test_fetch_dev(), test_fetch_hn() (+47 more)

### Community 1 - "GenAI SDK Internal Logic"
Cohesion: 0.05
Nodes (58): audioChunk(), close(), convertBidiSetupToTokenSetup(), createFunctionResponsePartFromBase64(), createFunctionResponsePartFromUri(), createModelContent(), createPartFromText(), createUserContent() (+50 more)

### Community 2 - "MLDev & Vertex Response Mapping"
Cohesion: 0.05
Nodes (56): blobToMldev$4(), candidateFromMldev(), citationMetadataFromMldev(), computeTokensResponseFromVertex(), countTokensResponseFromMldev(), countTokensResponseFromVertex(), createFileResponseFromMldev(), deleteCachedContentResponseFromMldev() (+48 more)

### Community 3 - "IntelAgent Core Components"
Cohesion: 0.05
Nodes (54): background.js Service Worker, Chrome extension icon click handler, Basic demo flow sequence, Dynamic MCP to Gemini tool binding, Fallback error handling pattern, genai.js bundled ES module, _LAST_DASHBOARD_HTML server cache, _CHART_REGISTRY (+46 more)

### Community 4 - "Vertex AI Job Management"
Cohesion: 0.05
Nodes (53): batchJobDestinationToVertex(), blobToMldev(), cancelTuningJobResponseFromMldev(), cancelTuningJobResponseFromVertex(), candidateFromMldev$1(), citationMetadataFromMldev$1(), contentEmbeddingFromVertex(), contentEmbeddingStatisticsFromVertex() (+45 more)

### Community 5 - "Part & Content Factory"
Cohesion: 0.06
Nodes (51): codeExecutionResult(), constructor(), createPartFromBase64(), createPartFromCodeExecutionResult(), createPartFromExecutableCode(), createPartFromFunctionCall(), createPartFromFunctionResponse(), createPartFromUri() (+43 more)

### Community 6 - "MLDev Configuration Transformers"
Cohesion: 0.06
Nodes (44): contentToMldev$1(), contentToMldev$3(), contentToMldev$4(), contentToVertex(), contentToVertex$2(), countTokensConfigToMldev(), countTokensConfigToVertex(), countTokensParametersToMldev() (+36 more)

### Community 7 - "Agent Curator Backend Handlers"
Cohesion: 0.08
Nodes (36): dashboard(), _fetch_dev(), _fetch_hn(), _fetch_reddit(), fetch_tech_news(), _load_library(), manage_local_library(), Read/write the local saved_articles.json library.      action='check_duplicates' (+28 more)

### Community 8 - "SDK Auth & Metadata Handling"
Cohesion: 0.09
Nodes (29): connect(), getApiKey(), getApiVersion(), getBaseUrl(), getCustomBaseUrl(), getDefaultHeaders(), getHeaders(), getLocation() (+21 more)

### Community 9 - "HTTP Request & Retry Logic"
Cohesion: 0.09
Nodes (23): asResponse(), calculateDefaultRetryTimeoutMillis(), CancelReadableStream(), defaultParseResponse(), fetchWithTimeout(), finally(), fromSSEResponse(), generate() (+15 more)

### Community 10 - "Streaming & SSE Processing"
Cohesion: 0.16
Nodes (22): __asyncGenerator(), __asyncValues(), __await(), callTool(), concatBytes(), decode(), decodeUTF8(), encodeUTF8() (+14 more)

### Community 11 - "Extension Sidepanel Controller"
Cohesion: 0.19
Nodes (15): appendGemini(), callMcpTool(), checkServer(), clearGemini(), loadMcpTools(), mcpInitialize(), mcpRequest(), mcpToolsToFunctionDeclarations() (+7 more)

### Community 12 - "Extension Dashboard Interface"
Cohesion: 0.2
Nodes (14): appendChatMessage(), callMcpTool(), checkServer(), loadMcpTools(), mcpInitialize(), mcpRequest(), mcpToolsToFunctionDeclarations(), parseSseResponse() (+6 more)

### Community 13 - "URL & Header Builders"
Cohesion: 0.12
Nodes (18): addAuthHeaders(), authHeaders(), baseURLOverridden(), buildBody(), buildHeaders(), buildRequest(), buildURL(), defaultIdempotencyKey() (+10 more)

### Community 14 - "Live Connectivity & Transcription"
Cohesion: 0.12
Nodes (17): audioTranscriptionConfigToMldev(), audioTranscriptionConfigToMldev$1(), contentToMldev(), contentToMldev$2(), contentToVertex$1(), createAuthTokenConfigToMldev(), createAuthTokenParametersToMldev(), generationConfigToVertex$1() (+9 more)

### Community 15 - "File Upload & Blob Management"
Cohesion: 0.16
Nodes (17): crossError(), download(), downloadFile(), fetchUploadUrl(), getBlobStat(), getFileName(), json(), sleep$1() (+9 more)

### Community 16 - "REST API Method Proxies"
Cohesion: 0.16
Nodes (15): create(), createCachedContentParametersToMldev(), createCachedContentParametersToVertex(), createFileSearchStoreConfigToMldev(), createFileSearchStoreParametersToMldev(), list(), methodRequest(), patch() (+7 more)

### Community 17 - "Image & Video Generation (MLDev)"
Cohesion: 0.17
Nodes (15): generatedImageFromMldev(), generatedVideoFromMldev(), generatedVideoFromVertex(), generateImagesResponseFromMldev(), generateVideosConfigToMldev(), generateVideosParametersToMldev(), generateVideosSourceToMldev(), imageFromMldev() (+7 more)

### Community 18 - "Multimodal Processing (Vertex)"
Cohesion: 0.2
Nodes (14): controlReferenceConfigToVertex(), generateVideosConfigToVertex(), generateVideosInternal(), generateVideosParametersToVertex(), generateVideosSourceToVertex(), imageToVertex(), maskReferenceConfigToVertex(), productImageToVertex() (+6 more)

### Community 19 - "Tuning & Dataset Management"
Cohesion: 0.15
Nodes (13): createFileParametersToMldev(), createInternal(), createTuningJobConfigToMldev(), createTuningJobParametersPrivateToMldev(), formatMap(), internalRegisterFilesParametersToMldev(), registerFiles(), registerFilesInternal() (+5 more)

### Community 20 - "Import & Batch Processing"
Cohesion: 0.17
Nodes (13): apiCall(), createTuningJobParametersPrivateToVertex(), importFile(), importFileConfigToMldev(), importFileParametersToMldev(), streamApiCall(), then(), tuneInternal() (+5 more)

### Community 21 - "Predict & Operations API"
Cohesion: 0.18
Nodes (13): fetchPredictOperationParametersToVertex(), fetchPredictVideosOperationInternal(), _fromAPIResponse(), get(), getBatchJobParametersToMldev(), getDocumentParametersToMldev(), getFileSearchStoreParametersToMldev(), getModelParametersToMldev() (+5 more)

### Community 22 - "Token & Content Generation"
Cohesion: 0.18
Nodes (12): computeTokens(), computeTokensParametersToVertex(), countTokens(), countTokensParametersToVertex(), deleteModelParametersToMldev(), generateContentInternal(), generateContentParametersToMldev(), generateContentParametersToVertex() (+4 more)

### Community 23 - "Job Cancellation & Deletion"
Cohesion: 0.2
Nodes (12): cancel(), cancelBatchJobParametersToMldev(), cancelBatchJobParametersToVertex(), cancelTuningJobParametersToMldev(), cancelTuningJobParametersToVertex(), delete(), deleteBatchJobParametersToMldev(), deleteBatchJobParametersToVertex() (+4 more)

### Community 24 - "Media Download & SDK Helpers"
Cohesion: 0.2
Nodes (10): downloadMedia(), editImageConfigToVertex(), editImageInternal(), editImageParametersInternalToVertex(), getInternal(), getTuningJobParametersToMldev(), getTuningJobParametersToVertex(), isVertexAI() (+2 more)

### Community 25 - "Low-level Request Routing"
Cohesion: 0.31
Nodes (9): constructUrl(), embedContentInternal(), getBaseResourcePath(), includeExtraHttpOptionsToRequestInit(), patchHttpOptions(), request(), requestStream(), shouldPrependVertexProjectPath() (+1 more)

### Community 26 - "Batch Job Configuration"
Cohesion: 0.22
Nodes (9): batchJobSourceToMldev(), batchJobSourceToVertex(), createBatchJobConfigToMldev(), createBatchJobConfigToVertex(), createBatchJobParametersToMldev(), createBatchJobParametersToVertex(), createInlinedGenerateContentRequest(), tBatchJobDestination() (+1 more)

### Community 27 - "Job State & History"
Cohesion: 0.29
Nodes (8): batchJobDestinationFromMldev(), batchJobDestinationFromVertex(), batchJobFromMldev(), batchJobFromVertex(), batchJobSourceFromVertex(), tJobState(), tRecvBatchJobDestination(), vertexMultimodalDatasetDestinationFromVertex()

### Community 28 - "Chat History & Messaging"
Cohesion: 0.29
Nodes (8): catch(), extractCuratedHistory(), getHistory(), isValidContent(), isValidResponse(), recordHistory(), sendMessage(), sendMessageStream()

### Community 29 - "Real-time Input & Audio"
Cohesion: 0.52
Nodes (7): liveSendRealtimeInputParametersToMldev(), liveSendRealtimeInputParametersToVertex(), sendRealtimeInput(), tAudioBlob(), tBlob(), tBlobs(), tImageBlob()

### Community 30 - "Video Ops (MLDev)"
Cohesion: 0.4
Nodes (5): generatedVideoFromMldev$1(), generatedVideoFromVertex$1(), tBytes$1(), videoFromMldev$1(), videoFromVertex$1()

### Community 31 - "Image Ops (Vertex)"
Cohesion: 0.4
Nodes (5): generatedImageFromVertex(), generatedImageMaskFromVertex(), generateImagesResponseFromVertex(), imageFromVertex(), safetyAttributesFromVertex()

### Community 32 - "File System Helpers"
Cohesion: 0.4
Nodes (5): getBytes(), getName(), makeFile(), propsForError(), toFile()

### Community 33 - "Embeddings Batch Jobs"
Cohesion: 0.5
Nodes (4): createEmbeddingsBatchJobConfigToMldev(), createEmbeddingsBatchJobParametersToMldev(), createEmbeddingsInternal(), embeddingsBatchJobSourceToMldev()

### Community 34 - "Recontextualization Ops"
Cohesion: 0.5
Nodes (4): recontextImage(), recontextImageConfigToVertex(), recontextImageParametersToVertex(), recontextImageSourceToVertex()

### Community 35 - "MLDev Request Fragmenting"
Cohesion: 0.5
Nodes (4): blobToMldev$2(), fileDataToMldev$2(), functionCallToMldev$2(), partToMldev$2()

### Community 36 - "MLDev Request Partials"
Cohesion: 0.5
Nodes (4): blobToMldev$1(), fileDataToMldev$1(), functionCallToMldev$1(), partToMldev$1()

### Community 37 - "Auth & Google Search Tools"
Cohesion: 0.5
Nodes (4): authConfigToMldev$1(), googleMapsToMldev$1(), googleSearchToMldev$1(), toolToMldev$1()

### Community 38 - "Tool Integration (MLDev)"
Cohesion: 0.5
Nodes (4): authConfigToMldev(), googleMapsToMldev(), googleSearchToMldev(), toolToMldev()

### Community 39 - "Tool Call Metadata"
Cohesion: 0.5
Nodes (4): authConfigToMldev$2(), googleMapsToMldev$2(), googleSearchToMldev$2(), toolToMldev$2()

### Community 40 - "Function Call Fragmenting"
Cohesion: 0.5
Nodes (4): blobToMldev$3(), fileDataToMldev$3(), functionCallToMldev$3(), partToMldev$3()

### Community 41 - "Search & Maps Tooling"
Cohesion: 0.5
Nodes (4): authConfigToMldev$3(), googleMapsToMldev$3(), googleSearchToMldev$3(), toolToMldev$3()

### Community 42 - "External Tool Providers"
Cohesion: 0.5
Nodes (4): authConfigToMldev$4(), googleMapsToMldev$4(), googleSearchToMldev$4(), toolToMldev$4()

### Community 43 - "Image Generation Logic"
Cohesion: 0.67
Nodes (3): generateImagesConfigToMldev(), generateImagesInternal(), generateImagesParametersToMldev()

## Ambiguous Edges - Review These
- `options.js Settings Page Script` → `saved_articles.json Local Library`  [AMBIGUOUS]
  extension/options.js · relation: semantically_similar_to

## Knowledge Gaps
- **40 isolated node(s):** `MCP server integration tests. Requires server running at http://localhost:8000.`, `Fetch from Hacker News (Algolia).`, `Fetch articles from multiple sources.      source: 'hn' (Hacker News), 'dev' (De`, `Read/write the local saved_articles.json library.      action='check_duplicates'`, `Lowercase type, convert labels/values simple format, normalize keys, enable lege` (+35 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `options.js Settings Page Script` and `saved_articles.json Local Library`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `getValueByPath()` connect `Vertex AI Job Management` to `GenAI SDK Internal Logic`, `MLDev & Vertex Response Mapping`, `Part & Content Factory`, `MLDev Configuration Transformers`, `Streaming & SSE Processing`, `Live Connectivity & Transcription`, `REST API Method Proxies`, `Image & Video Generation (MLDev)`, `Multimodal Processing (Vertex)`, `Tuning & Dataset Management`, `Import & Batch Processing`, `Predict & Operations API`, `Token & Content Generation`, `Job Cancellation & Deletion`, `Media Download & SDK Helpers`, `Batch Job Configuration`, `Job State & History`, `Real-time Input & Audio`, `Video Ops (MLDev)`, `Image Ops (Vertex)`, `Embeddings Batch Jobs`, `Recontextualization Ops`, `MLDev Request Fragmenting`, `MLDev Request Partials`, `Auth & Google Search Tools`, `Tool Integration (MLDev)`, `Tool Call Metadata`, `Function Call Fragmenting`, `Search & Maps Tooling`, `External Tool Providers`, `Image Generation Logic`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `setValueByPath()` connect `MLDev & Vertex Response Mapping` to `GenAI SDK Internal Logic`, `Vertex AI Job Management`, `Part & Content Factory`, `MLDev Configuration Transformers`, `Streaming & SSE Processing`, `Live Connectivity & Transcription`, `REST API Method Proxies`, `Image & Video Generation (MLDev)`, `Multimodal Processing (Vertex)`, `Tuning & Dataset Management`, `Import & Batch Processing`, `Predict & Operations API`, `Token & Content Generation`, `Job Cancellation & Deletion`, `Media Download & SDK Helpers`, `Batch Job Configuration`, `Job State & History`, `Real-time Input & Audio`, `Video Ops (MLDev)`, `Image Ops (Vertex)`, `Embeddings Batch Jobs`, `Recontextualization Ops`, `MLDev Request Fragmenting`, `MLDev Request Partials`, `Auth & Google Search Tools`, `Tool Integration (MLDev)`, `Tool Call Metadata`, `Function Call Fragmenting`, `Search & Maps Tooling`, `External Tool Providers`, `Image Generation Logic`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `MCP server integration tests. Requires server running at http://localhost:8000.`, `Fetch from Hacker News (Algolia).`, `Fetch articles from multiple sources.      source: 'hn' (Hacker News), 'dev' (De` to the rest of the system?**
  _40 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MCP Server Testing` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `GenAI SDK Internal Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `MLDev & Vertex Response Mapping` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._