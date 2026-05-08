function geminiHistoryToOpenAI(history, systemPrompt) {
  const messages = [{ role: "system", content: systemPrompt }];
  // Tracks name→id for matching tool responses to their call
  const toolCallIdMap = {};

  for (const turn of history) {
    const { role, parts } = turn;

    if (role === "user") {
      const textParts = parts.filter(p => p.text);
      const responseParts = parts.filter(p => p.functionResponse);

      if (responseParts.length > 0) {
        for (const part of responseParts) {
          const { name, response } = part.functionResponse;
          messages.push({
            role: "tool",
            tool_call_id: toolCallIdMap[name] || `call_${name}`,
            content: JSON.stringify(response.content ?? response),
          });
        }
      }
      if (textParts.length > 0) {
        messages.push({ role: "user", content: textParts.map(p => p.text).join("\n") });
      }
    } else if (role === "model") {
      const textParts = parts.filter(p => p.text);
      const funcParts = parts.filter(p => p.functionCall);

      if (funcParts.length > 0) {
        const toolCalls = funcParts.map((p, i) => {
          const id = `call_${p.functionCall.name}_${Date.now()}_${i}`;
          toolCallIdMap[p.functionCall.name] = id;
          return {
            id,
            type: "function",
            function: {
              name: p.functionCall.name,
              arguments: JSON.stringify(p.functionCall.args || {}),
            },
          };
        });
        messages.push({
          role: "assistant",
          content: textParts.map(p => p.text).join("") || null,
          tool_calls: toolCalls,
        });
      } else {
        messages.push({
          role: "assistant",
          content: textParts.map(p => p.text).join(""),
        });
      }
    }
  }

  return messages;
}

export class OllamaProvider {
  constructor(baseUrl, model, thinking = false) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.model = model;
    this.thinking = thinking;
  }

  async generateContent(conversationHistory, functionDeclarations, systemInstruction, forceFinish) {
    const messages = geminiHistoryToOpenAI(conversationHistory, systemInstruction);

    const tools = functionDeclarations.map(fn => ({
      type: "function",
      function: {
        name: fn.name,
        description: fn.description || "",
        parameters: fn.parameters || { type: "object", properties: {} },
      },
    }));

    const toolChoice = forceFinish
      ? { type: "function", function: { name: "render_dashboard" } }
      : "auto";

    const body = {
      model: this.model,
      messages,
      tools: tools.length ? tools : undefined,
      tool_choice: tools.length ? toolChoice : undefined,
      temperature: 0,
      stream: false,
      ...(this.thinking && { think: true }),
    };

    const res = await fetch(`${this.baseUrl}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Ollama error ${res.status}: ${errText}`);
    }

    const json = await res.json();
    const message = json.choices?.[0]?.message;
    if (!message) throw new Error("No message in Ollama response");

    if (this.thinking && message.thinking) {
      console.group("%c[Gemma Thinking]", "color:#a5d6ff;font-weight:bold");
      console.log(message.thinking);
      console.groupEnd();
    }

    const toolCalls = (message.tool_calls || []).map(tc => ({
      name: tc.function.name,
      args: (() => { try { return JSON.parse(tc.function.arguments || "{}"); } catch { return {}; } })(),
    }));

    const textParts = message.content || "";

    // Synthesize Gemini-format parts so conversationHistory stays uniform
    const rawModelParts = [];
    if (message.content) rawModelParts.push({ text: message.content });
    for (const tc of message.tool_calls || []) {
      rawModelParts.push({
        functionCall: {
          name: tc.function.name,
          args: (() => { try { return JSON.parse(tc.function.arguments || "{}"); } catch { return {}; } })(),
        },
      });
    }

    return { rawModelParts, toolCalls, textParts };
  }

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/api/tags`, {
        signal: AbortSignal.timeout(3000),
      });
      return res.ok;
    } catch {
      return false;
    }
  }
}
