export class GeminiProvider {
  constructor(ai, model) {
    this.ai = ai;
    this.model = model;
  }

  async generateContent(conversationHistory, functionDeclarations, systemInstruction, forceFinish) {
    const response = await this.ai.models.generateContent({
      model: this.model,
      contents: conversationHistory,
      config: {
        systemInstruction,
        tools: [
          { functionDeclarations: functionDeclarations.length ? functionDeclarations : [] },
          ...(forceFinish ? [] : [{ googleSearch: {} }]),
        ],
        toolConfig: {
          functionCallingConfig: forceFinish
            ? { mode: "ANY", allowedFunctionNames: ["render_dashboard"] }
            : { mode: "AUTO" },
          ...(!forceFinish && {
            googleSearchRetrieval: {
              dynamicRetrievalConfig: { mode: "DYNAMIC", dynamicThreshold: 0.3 },
            },
            includeServerSideToolInvocations: true,
          }),
        },
        generationConfig: { temperature: 0 },
      },
    });

    const candidate = response.candidates?.[0];
    if (!candidate) throw new Error("No candidates in Gemini response");

    const parts = candidate.content?.parts || [];
    const toolCalls = (response.functionCalls || []).map(c => ({ name: c.name, args: c.args }));
    const textParts = parts.map(p => p.text || "").join("\n").trim();

    return { rawModelParts: parts, toolCalls, textParts };
  }
}
