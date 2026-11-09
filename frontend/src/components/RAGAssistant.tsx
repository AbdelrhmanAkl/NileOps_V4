import React, { useState, useRef, useEffect } from "react";
import { useLanguage } from "../contexts/LanguageContext";
import { askBankingAssistant, RAGResponse, RAGCitation } from "../api/client";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  response?: RAGResponse;
  timestamp: string;
}

interface RAGAssistantProps {
  portalType: "customer" | "employee";
  mode?: "floating" | "embedded";
}

export const RAGAssistant: React.FC<RAGAssistantProps> = ({
  portalType,
  mode = "embedded",
}) => {
  const { isArabic } = useLanguage();
  const [isOpen, setIsOpen] = useState<boolean>(mode === "embedded");
  const [inputQuery, setInputQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedPassages, setExpandedPassages] = useState<Record<string, boolean>>({});
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-welcome",
      sender: "assistant",
      text: isArabic
        ? portalType === "employee"
          ? "مرحباً بك في المساعد الذكي لموظفي بنك النيل. يمكنك الاستفسار عن كافة اللوائح والسياسات الداخلية وإجراءات فحص الهوية ومكافحة غسل الأموال."
          : "مرحباً بك في المساعد المصرفي الذكي لبنك النيل. تفضل بطرح استفساراتك حول سياسات فتح الحسابات، الحدود الدنيا، المصاريف، أو الشروط المصرفية."
        : portalType === "employee"
        ? "Welcome to the NileOps Staff Policy Assistant. You can query internal operating policies, KYC verification rules, and AML guidelines."
        : "Welcome to the NileOps Banking Assistant. Ask any question regarding retail account opening, minimum balances, fees, or policy rules.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isLoading]);

  const togglePassage = (key: string) => {
    setExpandedPassages((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const sampleQuestions = isArabic
    ? portalType === "employee"
      ? [
          "كيف تحدد أرقام بطاقة الرقم القومي محافظة الميلاد؟",
          "ما هي معايير وضوابط فحص بطاقات الرقم القومي الاصطناعية؟",
          "سعر الدولار في السوق الموازي النهاردة كام؟", // Abstention probe
        ]
      : [
          "ما هو الحد الأدنى لفتح الحساب الجاري بالجنيه؟",
          "كم تبلغ غرامة انخفاض الرصيد عن الحد الأدنى شهرياً؟",
          "ازاي اعمل ملوخية بالفراخ على الطريقة المظبوطة؟", // Abstention probe
        ]
    : portalType === "employee"
    ? [
        "Which digits in Egyptian National IDs identify birth governorate?",
        "What are the compliance rules for synthetic National IDs?",
        "How do I fix a leaking water pipe under the kitchen sink?", // Abstention probe
      ]
    : [
        "What is the minimum opening balance for checking accounts?",
        "What monthly penalty applies if balance drops below minimum?",
        "What are the official rules for playing squash?", // Abstention probe
      ];

  const handleSend = async (queryToSend?: string) => {
    const q = (queryToSend || inputQuery).trim();
    if (!q || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await askBankingAssistant({
        query: q,
        portal_type: portalType,
        language: isArabic ? "ar" : "en",
        threshold: 0.15,
      });

      const assistantMsg: Message = {
        id: `asst-${Date.now()}`,
        sender: "assistant",
        text: response.answer,
        response: response,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setErrorMessage(
        err.message ||
          (isArabic
            ? "تعذر الاتصال بالمساعد الذكي للسياسات. يرجى المحاولة لاحقاً."
            : "Failed to connect to the policy assistant. Please try again.")
      );
    } finally {
      setIsLoading(false);
    }
  };

  const content = (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="bg-slate-800/90 border-b border-slate-700/80 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3 rtl:space-x-reverse">
          <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 font-bold">
            🤖
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              {isArabic
                ? portalType === "employee"
                  ? "المساعد الذكي للسياسات المصرفية (الموظفين)"
                  : "المساعد المصرفي الذكي (العملاء)"
                : portalType === "employee"
                ? "NileOps Staff Policy Assistant"
                : "NileOps AI Banking Assistant"}
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                {portalType === "employee" ? "STAFF VERIFIED" : "PUBLIC KB"}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              {isArabic
                ? "مدعوم بمحرك الاسترجاع الدلالي Qdrant والسياسات المصرفية المعتمدة"
                : "Grounded semantic retrieval powered by Qdrant & approved policy corpus"}
            </p>
          </div>
        </div>

        {mode === "floating" && (
          <button
            onClick={() => setIsOpen(false)}
            className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-700/50 transition-colors"
            title={isArabic ? "إغلاق" : "Close"}
          >
            ✕
          </button>
        )}
      </div>

      {/* Suggested Quick Questions */}
      <div className="bg-slate-800/40 border-b border-slate-700/40 px-4 py-2 flex items-center gap-2 overflow-x-auto text-xs">
        <span className="text-slate-400 font-medium whitespace-nowrap">
          {isArabic ? "أسئلة مقترحة:" : "Suggestions:"}
        </span>
        {sampleQuestions.map((sq, i) => (
          <button
            key={i}
            onClick={() => handleSend(sq)}
            disabled={isLoading}
            className="whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-700/60 hover:bg-teal-500/20 hover:text-teal-300 text-slate-300 border border-slate-600/50 transition-colors"
          >
            {sq}
          </button>
        ))}
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${
              m.sender === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-md ${
                m.sender === "user"
                  ? "bg-teal-600 text-white rounded-br-none"
                  : "bg-slate-800/90 text-slate-100 border border-slate-700/80 rounded-bl-none"
              }`}
            >
              {/* Abstention State Notice */}
              {m.response?.abstained && (
                <div className="mb-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-2">
                  <span className="text-base">⚠️</span>
                  <div>
                    <div className="font-semibold mb-0.5">
                      {isArabic ? "لم يتم العثور على سياسة معتمدة" : "No Supporting Policy Found"}
                    </div>
                    <div>
                      {isArabic
                        ? "هذا الاستفسار خارج نطاق اللوائح المصرفية المعتمدة للبنك. يرجى التواصل مع إدارة العمليات أو خدمة العملاء."
                        : "This inquiry falls outside the approved banking policy corpus. Strict thresholding prevented ungrounded hallucination."}
                    </div>
                  </div>
                </div>
              )}

              {/* Deterministic Fallback Banner */}
              {m.response && !m.response.abstained && m.response.fallback_used && (
                <div className="mb-3 p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs">
                  <div className="flex items-center gap-2 font-semibold text-blue-400 mb-1">
                    <span>⚡</span>
                    <span>
                      {isArabic
                        ? "استناد مباشر لنصوص السياسات المعتمدة (نظام الحماية البديل)"
                        : "Direct Policy Grounding (Deterministic Fallback)"}
                    </span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-blue-500/20 text-blue-300 font-mono">
                      fallback_used: true
                    </span>
                  </div>
                  <p className="text-[11px] text-blue-200/80">
                    {isArabic
                      ? "إشعار استرشادي: تم استخراج هذه الإجابة وتنسيقها مباشرة من نصوص السياسات المصرفية المعتمدة نظراً لعدم توفر خدمة التحليل التوليدي."
                      : "Advisory: This answer was extracted directly from approved policy texts via deterministic fallback because generative LLM reasoning was offline or timed out."}
                  </p>
                </div>
              )}

              {/* Answer Text */}
              <div className="whitespace-pre-wrap">{m.text}</div>

              {/* Citations & Source Passages */}
              {m.response && m.response.citations && m.response.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-700/60 space-y-2">
                  <div className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>{isArabic ? "المصادر والسياسات المعتمدة:" : "Verified Policy Citations:"}</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {m.response.citations.length} {isArabic ? "مرجع" : "source(s)"}
                    </span>
                  </div>

                  {m.response.citations.map((c: RAGCitation, idx: number) => {
                    const passageKey = `${m.id}-cit-${idx}`;
                    const isExpanded = !!expandedPassages[passageKey];

                    return (
                      <div
                        key={idx}
                        className="bg-slate-900/80 border border-slate-700/70 rounded-lg p-2.5 text-xs"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="px-1.5 py-0.5 rounded font-mono font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30 text-[11px]">
                              {c.code}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
                              v{c.version}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">
                              {c.domain}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-emerald-400">
                              score: {(c.score || 0).toFixed(3)}
                            </span>
                            {c.passage && (
                              <button
                                onClick={() => togglePassage(passageKey)}
                                className="text-[11px] font-medium text-teal-400 hover:text-teal-300 underline underline-offset-2 transition-colors"
                              >
                                {isExpanded
                                  ? isArabic
                                    ? "إخفاء النص"
                                    : "Hide Passage"
                                  : isArabic
                                  ? "عرض النص المصدري"
                                  : "Show Source Passage"}
                              </button>
                            )}
                          </div>
                        </div>

                        <div className="text-slate-300 font-medium mt-1">{c.title}</div>

                        {/* Expandable Passage Block */}
                        {isExpanded && c.passage && (
                          <div className="mt-2 p-2.5 rounded bg-slate-950 border border-teal-500/30 text-slate-300 text-xs leading-relaxed font-mono whitespace-pre-wrap animate-fadeIn">
                            <div className="text-[10px] text-teal-400 font-semibold mb-1 uppercase tracking-wide">
                              {isArabic ? "النص المصدري المعتمد:" : "Audited Source Passage:"}
                            </div>
                            {c.passage}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <span className="text-[10px] text-slate-500 mt-1 px-1">{m.timestamp}</span>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 rtl:space-x-reverse text-slate-400 text-xs p-3 bg-slate-800/50 rounded-xl w-fit border border-slate-700/50">
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-bounce" />
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-bounce [animation-delay:0.2s]" />
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-bounce [animation-delay:0.4s]" />
            <span>
              {isArabic
                ? "جاري استرجاع السياسات وتدقيق الإجابة..."
                : "Retrieving banking policies and verifying grounding..."}
            </span>
          </div>
        )}

        {errorMessage && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
            <span>{errorMessage}</span>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-rose-200 text-sm font-bold"
            >
              ✕
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-3 bg-slate-800/80 border-t border-slate-700/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
            placeholder={
              isArabic
                ? portalType === "employee"
                  ? "اسأل عن إجراءات فحص الرقم القومي، فتح الحسابات، سياسات العمليات..."
                  : "اسأل عن الحد الأدنى لفتح الحساب، المصاريف الشهرية، الفائدة..."
                : portalType === "employee"
                ? "Ask about Egyptian National ID rules, account guidelines, AML..."
                : "Ask about account opening minimums, monthly fees, interest..."
            }
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
          >
            <span>{isArabic ? "إرسال" : "Send"}</span>
            <span>➤</span>
          </button>
        </form>
      </div>
    </div>
  );

  if (mode === "embedded") {
    return <div className="h-[720px] w-full">{content}</div>;
  }

  // Floating Mode
  return (
    <>
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 rtl:right-auto rtl:left-6 z-50 flex items-center gap-2.5 px-4 py-3 bg-teal-600 hover:bg-teal-500 text-white rounded-full shadow-2xl transition-all duration-300 hover:scale-105 border border-teal-400/40"
        >
          <span className="text-xl">🤖</span>
          <span className="text-sm font-semibold">
            {isArabic ? "المساعد المصرفي الذكي" : "Ask NileOps AI"}
          </span>
        </button>
      )}

      {/* Floating Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 rtl:right-auto rtl:left-6 z-50 w-[440px] max-w-[calc(100vw-2rem)] h-[620px] max-h-[calc(100vh-6rem)] animate-fadeIn">
          {content}
        </div>
      )}
    </>
  );
};

