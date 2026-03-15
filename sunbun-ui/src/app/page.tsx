"use client";

/**
 * SunBun Solar Assistant Frontend
 * Modern Next.js interface that connects to the Aegra backend via LangGraph SDK.
 * Renders interactive buttons from message metadata.
 */

import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef } from "react";

// Helper to safely render message content (handles strings or message arrays)
const renderContent = (content: any): string => {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content.map(c => (typeof c === "string" ? c : JSON.stringify(c))).join(" ");
  }
  return JSON.stringify(content);
};

// Generate a fresh thread ID for each session
const generateThreadId = () => typeof crypto !== "undefined" 
  ? crypto.randomUUID() 
  : `thread-${Date.now()}-${Math.random().toString(36).slice(2)}`;

export default function SunBunChat() {
  const [threadId, setThreadId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Generate a unique thread ID on mount (client-side only)
  useEffect(() => {
    setThreadId(generateThreadId());
  }, []);
  
  // Connect to Aegra backend (only when threadId is ready)
  const chat = useStream<{ messages: Message[] }>({
    apiUrl: "http://127.0.0.1:2026",
    assistantId: "agent",
    threadId: threadId || undefined
  });

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollTop = messagesEndRef.current.scrollHeight;
    }
  }, [chat.messages, chat.isLoading]);

  const handleSend = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const text = formData.get("message") as string;

    if (text.trim()) {
      chat.submit({
        messages: [{ type: "human", content: text }],
      });
      e.currentTarget.reset();
    }
  };

  const handleButtonClick = (value: string, label: string) => {
    chat.submit({
      messages: [
        { 
          type: "human", 
          content: value, 
          additional_kwargs: { label } as any 
        }
      ],
    });
  };

  // Start a completely new conversation
  const handleNewChat = () => {
    setThreadId(generateThreadId());
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-6 bg-gradient-to-br from-orange-50 to-yellow-50">
      
      {/* Header */}
      <div className="bg-white shadow-lg rounded-t-2xl p-6 border-b-4 border-orange-500">
        <div className="flex items-center gap-4">
          <div className="text-5xl">🌞</div>
          <div>
            <h1 className="text-3xl font-bold text-gray-800">SunBun Solar</h1>
            <p className="text-gray-600">AI-Powered Sales & Service Assistant</p>
          </div>
        </div>
        
        {/* Thread ID display + New Chat */}
        <div className="mt-4 flex items-center justify-between">
          {threadId && (
            <div className="text-sm text-gray-500 font-mono bg-gray-100 p-2 rounded">
              Session: {threadId.substring(0, 8)}...
            </div>
          )}
          <button
            onClick={handleNewChat}
            className="text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1.5 rounded-lg transition-all"
          >
            🔄 New Chat
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto bg-white shadow-lg p-6 space-y-4" ref={messagesEndRef}>
        {(() => {
          const messages = chat.messages || [];
          // Find index of the LAST AI message (any type, not just ones with buttons)
          let lastAiIdx = -1;
          messages.forEach((m, i) => {
            if (m.type !== "human") {
              lastAiIdx = i;
            }
          });

          return messages.map((msg, idx) => {
            const msgAny = msg as any;
            const options = msgAny.additional_kwargs?.metadata?.options || null;
            const isLatestButtons = idx === lastAiIdx;

            return (
              <div
                key={msg.id || idx}
                className={`flex ${msg.type === "human" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[75%] rounded-2xl p-4 shadow-md ${
                    msg.type === "human"
                      ? "bg-blue-600 text-white"
                      : "bg-white border-2 border-gray-200"
                  }`}
                >
                  {/* Message Header */}
                  <div className={`text-xs font-semibold mb-2 ${
                    msg.type === "human" ? "text-blue-100" : "text-orange-600"
                  }`}>
                    {msg.type === "human" ? "YOU" : "🌞 SUNBUN ASSISTANT"}
                  </div>
                  
                  <div className={`whitespace-pre-wrap ${
                    msg.type === "human" ? "text-white" : "text-gray-800"
                  }`}>
                    {msgAny.additional_kwargs?.label || renderContent(msg.content)}
                  </div>

                  {/* Interactive Buttons - only active on latest bot message */}
                  {options && Array.isArray(options) && (
                    <div className="mt-4 pt-3 border-t border-gray-200 flex flex-wrap gap-2">
                      {options.map((opt: { label: string; value: string }, index: number) => (
                        <button
                          key={index}
                          onClick={() => isLatestButtons && handleButtonClick(opt.value, opt.label)}
                          disabled={!isLatestButtons}
                          className={isLatestButtons
                            ? "bg-gradient-to-r from-orange-500 to-yellow-500 hover:from-orange-600 hover:to-yellow-600 text-white font-semibold px-4 py-2 rounded-lg transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                            : "bg-gray-300 text-gray-500 font-semibold px-4 py-2 rounded-lg cursor-not-allowed opacity-60"
                          }
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          });
        })()}


        {/* Loading Indicator */}
        {chat.isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border-2 border-gray-200 rounded-2xl p-4 shadow-md">
              <div className="flex items-center gap-2 text-gray-600">
                <div className="animate-spin h-4 w-4 border-2 border-orange-500 border-t-transparent rounded-full"></div>
                <span>SunBun is thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <form 
        onSubmit={handleSend} 
        className="bg-white shadow-lg rounded-b-2xl p-4 flex gap-3 border-t-2 border-gray-200"
      >
        <input
          name="message"
          type="text"
          placeholder="Type your message or use the buttons above..."
          className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent text-black placeholder:text-black"
          disabled={chat.isLoading}
        />
        <button
          type="submit"
          disabled={chat.isLoading}
          className="bg-gradient-to-r from-orange-500 to-yellow-500 hover:from-orange-600 hover:to-yellow-600 disabled:from-gray-300 disabled:to-gray-400 text-white font-bold px-8 py-3 rounded-xl transition-all shadow-md hover:shadow-lg"
        >
          Send
        </button>
      </form>
    </div>
  );
}
