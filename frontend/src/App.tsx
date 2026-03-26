import { useState } from "react";

function App() {
    const [message, setMessage] = useState("");
    const [chatHistory, setChatHistory] = useState<
        { role: string; content: string }[]
    >([]);
    const [isLoading, setIsLoading] = useState(false);

    const sendMessage = async () => {
        if (!message.trim()) return;

        const newHistory = [...chatHistory, { role: "user", content: message }];
        setChatHistory(newHistory);
        setMessage("");
        setIsLoading(true);

        try {
            const response = await fetch("http://localhost:8001/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: message,
                    thread_id: "taha_web_1",
                }),
            });

            if (!response.ok) throw new Error("API hatası");

            const data = await response.json();
            setChatHistory([
                ...newHistory,
                { role: "agent", content: data.response },
            ]);
        } catch (error) {
            console.error("Hata:", error);
            setChatHistory([
                ...newHistory,
                {
                    role: "agent",
                    content: "Sisteme ulaşılamıyor. Sunucu açık mı?",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4 text-gray-800 font-sans">
            {/* Ana Sohbet Konteyneri */}
            <div className="w-full max-w-3xl bg-white rounded-3xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-[85vh]">
                {/* Üst Bilgi (Header) */}
                <div className="bg-white/80 backdrop-blur-md border-b border-gray-100 p-5 text-center">
                    <h1 className="text-xl font-semibold tracking-tight text-gray-900">
                        Research Agent
                    </h1>
                    <p className="text-xs text-gray-400 mt-1 font-medium tracking-wide uppercase">
                        Otonom Araştırma Asistanı
                    </p>
                </div>

                {/* Mesajlaşma Alanı */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/30">
                    {chatHistory.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
                            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-3xl">
                                🤖
                            </div>
                            <p className="text-sm font-medium">
                                Araştırmaya başlamak için bir konu yazın.
                            </p>
                        </div>
                    )}

                    {chatHistory.map((msg, index) => (
                        <div
                            key={index}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div
                                className={`max-w-[80%] px-5 py-3.5 text-sm leading-relaxed ${
                                    msg.role === "user"
                                        ? "bg-black text-white rounded-2xl rounded-br-sm shadow-md"
                                        : "bg-white text-gray-800 border border-gray-200 shadow-sm rounded-2xl rounded-bl-sm"
                                }`}
                            >
                                {msg.content}
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-white border border-gray-200 shadow-sm rounded-2xl rounded-bl-sm px-5 py-4 flex space-x-2 items-center">
                                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-75"></div>
                                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-150"></div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Girdi (Input) Alanı */}
                <div className="p-4 bg-white border-t border-gray-100">
                    <div className="relative flex items-center">
                        <input
                            type="text"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyDown={(e) =>
                                e.key === "Enter" && sendMessage()
                            }
                            placeholder="Araştırılacak konuyu veya soruyu buraya yazın..."
                            disabled={isLoading}
                            className="w-full bg-gray-100 border border-transparent focus:bg-white focus:border-gray-300 focus:ring-0 rounded-full pl-6 pr-14 py-4 text-sm outline-none transition-all disabled:opacity-50"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={isLoading || !message.trim()}
                            className="absolute right-2 p-2.5 bg-black text-white rounded-full hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="currentColor"
                                className="w-4 h-4"
                            >
                                <path d="M3.478 2.404a.75.75 0 00-.926.941l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94h.01l19.5-8.25a.75.75 0 000-1.39l-19.5-8.25z" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
