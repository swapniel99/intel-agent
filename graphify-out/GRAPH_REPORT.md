# Graph Report - intel-agent  (2026-05-21)

## Corpus Check
- 16 files · ~100,698 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1001 nodes · 3225 edges · 93 communities (69 shown, 24 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8dca2d53`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- [[_COMMUNITY_Options Page Interaction|Options Page Interaction]]
- [[_COMMUNITY_Options UI Form|Options UI Form]]
- [[_COMMUNITY_PRD Specification|PRD Specification]]
- [[_COMMUNITY_Architecture Documentation|Architecture Documentation]]
- [[_COMMUNITY_Claude Architecture Guide|Claude Architecture Guide]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]

## God Nodes (most connected - your core abstractions)
1. `getValueByPath()` - 318 edges
2. `setValueByPath()` - 306 edges
3. `isVertexAI()` - 47 edges
4. `_parse()` - 40 edges
5. `_call()` - 40 edges
6. `request()` - 38 edges
7. `then()` - 36 edges
8. `tModel()` - 34 edges
9. `formatMap()` - 31 edges
10. `get()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `options.js Settings Page Script` --semantically_similar_to--> `saved_articles.json Local Library`  [AMBIGUOUS] [semantically similar]
  extension/options.js → saved_articles.json
- `dashboard GET Route` --rationale_for--> `Dashboard iframe Rendering Pattern`  [EXTRACTED]
  main.py → extension/sidepanel.html
- `Agentic Loop` --rationale_for--> `Basic demo flow sequence`  [EXTRACTED]
  extension/sidepanel.js → CLAUDE.md
- `callMcpTool function` --rationale_for--> `FastMCP CORS middleware`  [INFERRED]
  extension/sidepanel.js → main.py
- `Fallback to saved_articles.json on network failure` --references--> `saved_articles.json Local Library`  [INFERRED]
  main.py → saved_articles.json

## Communities (93 total, 24 thin omitted)

### Community 0 - "MCP Server Testing"
Cohesion: 0.08
Nodes (71): _call(), _parse(), MCP server integration tests. Requires server running at http://localhost:8000., test_dashboard_route_dark(), test_dashboard_route_light(), test_fetch_all_sources(), test_fetch_dev(), test_fetch_hn() (+63 more)

### Community 1 - "GenAI SDK Internal Logic"
Cohesion: 0.04
Nodes (62): blobToMldev(), candidateFromMldev(), citationMetadataFromMldev(), createFileParametersToMldev(), createTuningJobConfigToMldev(), createTuningJobParametersPrivateToMldev(), deleteCachedContentResponseFromMldev(), deleteCachedContentResponseFromVertex() (+54 more)

### Community 2 - "MLDev & Vertex Response Mapping"
Cohesion: 0.15
Nodes (15): background.js Service Worker, callMcpTool, checkServer, Gemini googleSearch Native Tool, sidepanel.html Side Panel UI, initGemini, loadMcpTools, loadSettings (+7 more)

### Community 3 - "IntelAgent Core Components"
Cohesion: 0.07
Nodes (29): audioChunk(), close(), createFunctionResponsePartFromBase64(), createFunctionResponsePartFromUri(), createPartFromCodeExecutionResult(), createPartFromFunctionCall(), createPartFromUri(), data() (+21 more)

### Community 4 - "Vertex AI Job Management"
Cohesion: 0.04
Nodes (59): blobToMldev$4(), cancelTuningJobResponseFromMldev(), cancelTuningJobResponseFromVertex(), candidateFromMldev$1(), citationMetadataFromMldev$1(), computeTokensResponseFromVertex(), contentEmbeddingFromVertex(), contentEmbeddingStatisticsFromVertex() (+51 more)

### Community 5 - "Part & Content Factory"
Cohesion: 0.06
Nodes (30): codeExecutionResult(), createPartFromBase64(), createPartFromExecutableCode(), createPartFromFunctionResponse(), error, executableCode(), findAfcIncompatibleToolIndexes(), functionCalls() (+22 more)

### Community 6 - "MLDev Configuration Transformers"
Cohesion: 0.22
Nodes (10): _fetch_dev(), _fetch_reddit(), fetch_tech_news(), _load_library(), manage_local_library(), Read/write the local saved_articles.json library.      action='check_duplicates', Read/write the local saved_articles.json library.      action='check_duplicates', Fetch articles from multiple sources.      source: 'hn' (Hacker News), 'dev' (De (+2 more)

### Community 7 - "Agent Curator Backend Handlers"
Cohesion: 0.07
Nodes (31): audioTranscriptionConfigToMldev(), audioTranscriptionConfigToMldev$1(), contentToMldev(), contentToMldev$2(), contentToMldev$4(), contentToVertex$1(), createAuthTokenConfigToMldev(), createAuthTokenParametersToMldev() (+23 more)

### Community 8 - "SDK Auth & Metadata Handling"
Cohesion: 0.15
Nodes (14): asResponse(), concatBytes(), decode(), decodeUTF8(), encodeUTF8(), finally(), findNewlineIndex(), flush() (+6 more)

### Community 9 - "HTTP Request & Retry Logic"
Cohesion: 0.12
Nodes (20): generatedImageFromMldev(), generatedVideoFromMldev(), generatedVideoFromMldev$1(), generatedVideoFromVertex(), generatedVideoFromVertex$1(), generateImagesResponseFromMldev(), generateVideosConfigToMldev(), generateVideosParametersToMldev() (+12 more)

### Community 10 - "Streaming & SSE Processing"
Cohesion: 0.07
Nodes (84): __asyncGenerator(), __asyncValues(), __await(), callTool(), cancel(), cancelBatchJobParametersToMldev(), cancelBatchJobParametersToVertex(), cancelTuningJobParametersToMldev() (+76 more)

### Community 11 - "Extension Sidepanel Controller"
Cohesion: 0.13
Nodes (15): calculateDefaultRetryTimeoutMillis(), CancelReadableStream(), defaultParseResponse(), fetchWithTimeout(), fromSSEResponse(), generate(), isAbortError(), loggerFor() (+7 more)

### Community 12 - "Extension Dashboard Interface"
Cohesion: 0.40
Nodes (5): listModelsConfigToMldev(), listModelsConfigToVertex(), listModelsParametersToMldev(), listModelsParametersToVertex(), tModelsUrl()

### Community 13 - "URL & Header Builders"
Cohesion: 0.15
Nodes (16): contentToMldev$1(), contentToVertex(), contentToVertex$2(), countTokensConfigToVertex(), createCachedContentConfigToVertex(), embedContentConfigToMldev(), embedContentConfigToVertex(), embedContentParametersPrivateToMldev() (+8 more)

### Community 14 - "Live Connectivity & Transcription"
Cohesion: 0.19
Nodes (15): appendGemini(), callMcpTool(), checkServer(), clearGemini(), loadMcpTools(), mcpInitialize(), mcpRequest(), mcpToolsToFunctionDeclarations() (+7 more)

### Community 15 - "File Upload & Blob Management"
Cohesion: 0.09
Nodes (29): connect(), getApiKey(), getApiVersion(), getBaseUrl(), getCustomBaseUrl(), getDefaultHeaders(), getHeaders(), getLocation() (+21 more)

### Community 16 - "REST API Method Proxies"
Cohesion: 0.25
Nodes (9): appendChatMessage(), isProviderReady(), mcpToolsToFunctionDeclarations(), renderDashboard(), resetConnection(), runAgent(), setServerStatus(), setStatus() (+1 more)

### Community 17 - "Image & Video Generation (MLDev)"
Cohesion: 0.16
Nodes (14): baseURLOverridden(), buildBody(), buildHeaders(), buildRequest(), buildURL(), defaultIdempotencyKey(), defaultQuery(), getUserAgent() (+6 more)

### Community 18 - "Multimodal Processing (Vertex)"
Cohesion: 0.29
Nodes (8): json(), sleep$1(), throwErrorIfNotOK(), uploadBlob(), uploadBlobInternal(), uploadBlobToFileSearchStore(), uploadToFileSearchStoreOperationFromMldev(), uploadToFileSearchStoreResponseFromMldev()

### Community 19 - "Tuning & Dataset Management"
Cohesion: 0.04
Nodes (44): $apiKeyInput, $chatHistory, $chatPanel, checkpoint, cleanUrl, $clearBtn, conversationCheckpoints, conversationHistory (+36 more)

### Community 20 - "Import & Batch Processing"
Cohesion: 0.08
Nodes (20): Change 1: System prompt — add intent class, Change 2: Quick-action preset buttons, Client Changes (extension/index.js), code:python (# New — for sentiment (richer fields than existing _fetch_re), code:block5 (- MARKETING_INTEL: brand sentiment, competitor comparison, c), code:toml ("duckduckgo-search>=8.0.0",), Constraints, Deps to Add (pyproject.toml) (+12 more)

### Community 22 - "Token & Content Generation"
Cohesion: 0.50
Nodes (4): createTuningJobConfigToVertex(), createTuningJobParametersPrivateToVertex(), tuningDatasetToVertex(), tuningValidationDatasetToVertex()

### Community 23 - "Job Cancellation & Deletion"
Cohesion: 0.10
Nodes (20): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+12 more)

### Community 24 - "Media Download & SDK Helpers"
Cohesion: 0.33
Nodes (6): addAuthHeaders(), authHeaders(), getAuthHeaders(), getHeadersInternal(), includeExtraBodyToRequestInit(), includeExtraHttpOptionsToRequestInit()

### Community 25 - "Low-level Request Routing"
Cohesion: 0.14
Nodes (12): Architecture, Backend (Python 3.14 + FastMCP), CI/CD, Code Patterns, code:bash (# Backend — one-time setup), code:block2 (intel-agent/), Frontend (Chrome Extension — Manifest V3), graphify (+4 more)

### Community 26 - "Batch Job Configuration"
Cohesion: 0.29
Nodes (8): batchJobDestinationFromMldev(), batchJobDestinationFromVertex(), batchJobFromMldev(), batchJobFromVertex(), batchJobSourceFromVertex(), tJobState(), tRecvBatchJobDestination(), vertexMultimodalDatasetDestinationFromVertex()

### Community 27 - "Job State & History"
Cohesion: 0.12
Nodes (17): apiCall(), constructor(), constructUrl(), getBaseResourcePath(), getDefaultFetch(), getRequestUrl(), getRequestUrlInternal(), hasNextPage() (+9 more)

### Community 28 - "Chat History & Messaging"
Cohesion: 0.52
Nodes (7): liveSendRealtimeInputParametersToMldev(), liveSendRealtimeInputParametersToVertex(), sendRealtimeInput(), tAudioBlob(), tBlob(), tBlobs(), tImageBlob()

### Community 29 - "Real-time Input & Audio"
Cohesion: 0.29
Nodes (8): catch(), extractCuratedHistory(), getHistory(), isValidContent(), isValidResponse(), recordHistory(), sendMessage(), sendMessageStream()

### Community 30 - "Video Ops (MLDev)"
Cohesion: 0.14
Nodes (13): 1. Backend Setup (MCP Server), 2. Frontend Setup (Chrome Extension), 🏗️ Architecture, code:mermaid (graph TD), code:bash (# Clone the repo), Dashboard Features, 🚀 Getting Started, 🛠️ Integrated Tools (+5 more)

### Community 31 - "Image Ops (Vertex)"
Cohesion: 0.40
Nodes (5): generatedImageFromVertex(), generatedImageMaskFromVertex(), generateImagesResponseFromVertex(), imageFromVertex(), safetyAttributesFromVertex()

### Community 32 - "File System Helpers"
Cohesion: 0.40
Nodes (5): getBytes(), getName(), makeFile(), propsForError(), toFile()

### Community 33 - "Embeddings Batch Jobs"
Cohesion: 0.50
Nodes (4): authConfigToMldev$2(), googleMapsToMldev$2(), googleSearchToMldev$2(), toolToMldev$2()

### Community 34 - "Recontextualization Ops"
Cohesion: 0.26
Nodes (13): Fallback error handling pattern, Fallback to saved_articles.json on network failure, _fetch_dev, _fetch_hn, _fetch_reddit, fetch_tech_news MCP Tool, _load_library, manage_local_library MCP Tool (+5 more)

### Community 35 - "MLDev Request Fragmenting"
Cohesion: 0.50
Nodes (4): authConfigToMldev(), googleMapsToMldev(), googleSearchToMldev(), toolToMldev()

### Community 36 - "MLDev Request Partials"
Cohesion: 0.50
Nodes (4): authConfigToMldev$3(), googleMapsToMldev$3(), googleSearchToMldev$3(), toolToMldev$3()

### Community 37 - "Auth & Google Search Tools"
Cohesion: 0.50
Nodes (4): authConfigToMldev$1(), googleMapsToMldev$1(), googleSearchToMldev$1(), toolToMldev$1()

### Community 38 - "Tool Integration (MLDev)"
Cohesion: 0.50
Nodes (4): authConfigToMldev$4(), googleMapsToMldev$4(), googleSearchToMldev$4(), toolToMldev$4()

### Community 39 - "Tool Call Metadata"
Cohesion: 0.13
Nodes (20): controlReferenceConfigToVertex(), generateVideosConfigToVertex(), generateVideosParametersToVertex(), generateVideosSourceToVertex(), imageToVertex(), maskReferenceConfigToVertex(), productImageToVertex(), recontextImageConfigToVertex() (+12 more)

### Community 40 - "Function Call Fragmenting"
Cohesion: 0.29
Nodes (7): createEmbeddingsBatchJobConfigToMldev(), createEmbeddingsBatchJobParametersToMldev(), embedContentBatchToMldev(), embedContentConfigToMldev$1(), embeddingsBatchJobSourceToMldev(), moveValueByPath(), _moveValueRecursive()

### Community 41 - "Search & Maps Tooling"
Cohesion: 0.17
Nodes (12): _build_chart_node(), _normalize_chart(), Lowercase type, convert labels/values simple format, normalize keys, enable lege, Lowercase type, convert labels/values simple format, normalize keys, enable lege, Convert normalized chart dict to Prefab JSON chart node., Convert normalized chart dict to Prefab JSON chart node., Render a dashboard. Always call this when finished — it is the only output surfa, Render a dashboard. Always call this when finished — it is the only output surfa (+4 more)

### Community 42 - "External Tool Providers"
Cohesion: 0.18
Nodes (11): batchJobDestinationToVertex(), batchJobSourceToMldev(), batchJobSourceToVertex(), createBatchJobConfigToMldev(), createBatchJobConfigToVertex(), createBatchJobParametersToMldev(), createBatchJobParametersToVertex(), createInlinedGenerateContentRequest() (+3 more)

### Community 43 - "Image Generation Logic"
Cohesion: 0.20
Nodes (10): Basic demo flow sequence, Dynamic MCP to Gemini tool binding, genai.js bundled ES module, Manifest V3 security & permissions, FastMCP CORS middleware, API key settings page, Agentic Loop, callMcpTool function (+2 more)

### Community 46 - "Options Page Interaction"
Cohesion: 0.29
Nodes (6): $apiKeyInput, $btn, key, $mcpUrlInput, settings, $status

### Community 51 - "Community 51"
Cohesion: 0.27
Nodes (10): _LAST_DASHBOARD_HTML server cache, _CHART_REGISTRY, CORSMiddleware Configuration, dashboard GET Route, _LAST_DASHBOARD_HTML Cache, render_prefab_dashboard MCP Tool, _TOPIC_PALETTES, Dashboard iframe Rendering Pattern (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.22
Nodes (9): deleteCachedContentParametersToMldev(), deleteCachedContentParametersToVertex(), getCachedContentParametersToMldev(), getCachedContentParametersToVertex(), tCachedContentName(), updateCachedContentConfigToMldev(), updateCachedContentConfigToVertex(), updateCachedContentParametersToMldev() (+1 more)

### Community 53 - "Community 53"
Cohesion: 0.22
Nodes (9): _bucket_top_posts(), fetch_brand_sentiment(), _fetch_reddit_sentiment(), _fetch_twitter_api(), Fetch tweets via Twitter API v2 recent search. Requires TWITTER_BEARER_TOKEN in, Returns (aggregate_dict, per_text_labels) — single model pass., Return up to n posts per sentiment label (neg first), tagged with sentiment. If, Fetch social media sentiment for pharma brands from Reddit, Twitter/X, and Linke (+1 more)

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (7): _fetch_dev(), _fetch_hn(), _fetch_reddit(), fetch_tech_news(), Fetch articles from multiple sources.      source: 'hn' (Hacker News), 'dev' (De, Fetch from Hacker News (Algolia)., Primary tool for DEVELOPER TRENDS and COMMUNITY DISCUSSION.     Use this for: "W

### Community 55 - "Community 55"
Cohesion: 0.33
Nodes (6): deleteFileParametersToMldev(), getFileParametersToMldev(), _isFile(), isGeneratedVideo(), isVideo(), tFileName()

### Community 56 - "Community 56"
Cohesion: 0.40
Nodes (6): callMcpTool(), checkServer(), loadMcpTools(), mcpInitialize(), mcpRequest(), parseSseResponse()

### Community 58 - "Community 58"
Cohesion: 0.40
Nodes (5): _load_library(), manage_local_library(), Read/write the local saved_articles.json library.      action='check_duplicates', Read/write the local saved_articles.json library.      action='check_duplicates', _save_library()

### Community 59 - "Community 59"
Cohesion: 0.40
Nodes (5): createModelContent(), createPartFromText(), createUserContent(), _isPart(), _toParts()

### Community 60 - "Community 60"
Cohesion: 0.40
Nodes (5): pause(), play(), resetContext(), sendPlaybackControl(), stop()

### Community 61 - "Community 61"
Cohesion: 0.50
Nodes (4): Chrome extension icon click handler, Dashboard iframe injection, Side panel HTML structure, Theme toggle UI

### Community 62 - "Community 62"
Cohesion: 0.50
Nodes (4): blobToMldev$1(), fileDataToMldev$1(), functionCallToMldev$1(), partToMldev$1()

### Community 63 - "Community 63"
Cohesion: 0.50
Nodes (4): blobToMldev$2(), fileDataToMldev$2(), functionCallToMldev$2(), partToMldev$2()

### Community 64 - "Community 64"
Cohesion: 0.50
Nodes (4): blobToMldev$3(), fileDataToMldev$3(), functionCallToMldev$3(), partToMldev$3()

### Community 65 - "Community 65"
Cohesion: 0.50
Nodes (4): flattenTypeArrayToAnyOf(), processJsonSchema(), tSchema(), tTool()

### Community 66 - "Community 66"
Cohesion: 0.50
Nodes (4): hasField(), listModelsResponseFromMldev(), listModelsResponseFromVertex(), tExtractModels()

### Community 67 - "Community 67"
Cohesion: 0.50
Nodes (4): tTuningJobStatus(), tunedModelFromMldev(), tuningJobFromMldev(), tuningJobFromVertex()

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (4): dashboard(), Serve last rendered Prefab dashboard HTML with theme support., Serve last rendered Prefab dashboard HTML with theme support., Serve last rendered Prefab dashboard HTML with theme support.

### Community 70 - "Community 70"
Cohesion: 0.50
Nodes (4): _ddgs_text_with_fallback(), fetch_search_presence(), Try primary backend aggressively; only fall back if it consistently fails., Check where pharma brands appear in search results for given keywords.      bran

### Community 71 - "Community 71"
Cohesion: 0.67
Nodes (3): dashboard(), Serve last rendered Prefab dashboard HTML with theme support., Serve last rendered Prefab dashboard HTML with theme support.

### Community 72 - "Community 72"
Cohesion: 0.67
Nodes (3): Compile curated articles and data into a professional dashboard.      Each card:, Compile curated articles and data into a professional dashboard.      Each card:, render_prefab_dashboard()

### Community 74 - "Community 74"
Cohesion: 0.67
Nodes (3): formatDestination(), getBigqueryUri(), getGcsUri()

### Community 75 - "Community 75"
Cohesion: 0.67
Nodes (3): _fetch_hn(), Fetch from Hacker News (Algolia)., Fetch from Hacker News (Algolia).

## Ambiguous Edges - Review These
- `options.js Settings Page Script` → `saved_articles.json Local Library`  [AMBIGUOUS]
  extension/options.js · relation: semantically_similar_to

## Knowledge Gaps
- **122 isolated node(s):** `u8`, `error`, `invalidSegments`, `path3`, `hasLeadingSlash` (+117 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `options.js Settings Page Script` and `saved_articles.json Local Library`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `list()` connect `Streaming & SSE Processing` to `IntelAgent Core Components`, `Community 53`, `Part & Content Factory`, `Community 70`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `fetch_brand_sentiment()` connect `Community 53` to `Streaming & SSE Processing`, `MLDev Configuration Transformers`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `_ddgs_text_with_fallback()` connect `Community 70` to `Streaming & SSE Processing`, `MLDev Configuration Transformers`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `MCP server integration tests. Requires server running at http://localhost:8000.`, `Fetch tweets via Twitter API v2 recent search. Requires TWITTER_BEARER_TOKEN in`, `Returns (aggregate_dict, per_text_labels) — single model pass.` to the rest of the system?**
  _163 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MCP Server Testing` be split into smaller, more focused modules?**
  _Cohesion score 0.07792207792207792 - nodes in this community are weakly interconnected._
- **Should `GenAI SDK Internal Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.04177683765203596 - nodes in this community are weakly interconnected._