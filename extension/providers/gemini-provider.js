export class GeminiProvider {
  constructor(ai, model, thinkingLevel = null) {
    this.ai = ai;
    this.model = model;
    this.thinkingLevel = thinkingLevel; // null=off, "MINIMAL"|"LOW"|"MEDIUM"|"HIGH"
  }

  async generateContent(conversationHistory, functionDeclarations, systemInstruction, forceFinish) {
    const config = {
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
    };

    if (this.thinkingLevel) {
      config.thinkingConfig = { thinkingLevel: this.thinkingLevel };
    }

    const response = await this.ai.models.generateContent({
      model: this.model,
      contents: conversationHistory,
      config,
    });

    const candidate = response.candidates?.[0];
    if (!candidate) throw new Error("No candidates in Gemini response");

    const parts = candidate.content?.parts || [];
    const toolCalls = (response.functionCalls || []).map(c => ({ name: c.name, args: c.args }));
    const textParts = parts
      .filter(p => !p.thought)
      .map(p => p.text || "")
      .join("\n")
      .trim();

    return { rawModelParts: parts, toolCalls, textParts };
  }
}
