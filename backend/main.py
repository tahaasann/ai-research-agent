import os
import logging
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langgraph.prebuilt import ToolNode
from langchain_litellm import ChatLiteLLM
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

load_dotenv()
logging.basicConfig(level=logging.INFO)

# --- 1. ARAÇLAR (TOOLS) ---
search_engine = DuckDuckGoSearchResults(max_results=3)


@tool
def web_search(query: str):
    """İnternette güncel bilgi aramak için kullanılır."""
    return search_engine.run(query)


tools = [web_search]


# --- 3. HAFIZA (STATE) ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# --- 4. AJANLAR (NODES - İŞÇİLER) ---


def researcher_agent(
    state: AgentState, config: RunnableConfig
):  # dict yerine RunnableConfig
    # Kullanıcının gönderdiği key'i al
    api_key = config.get("configurable", {}).get("api_key")
    llm = ChatLiteLLM(model="gpt-4o", api_key=api_key).bind_tools(tools)

    sys_msg = SystemMessage(
        content="""Sen usta bir Veri Araştırmacısısın. 
        Görevin, kullanıcıdan gelen konu hakkında interneti kullanarak en güncel, en derinlemesine ham verileri toplamaktır. 
        Asla makale yazma. Sadece ham veriyi, istatistikleri ve gerçekleri liste halinde sun."""
    )
    messages = [sys_msg] + state["messages"]

    # DİKKAT: researcher_llm değil, yukarıda tanımladığımız llm'i kullanıyoruz!
    response = llm.invoke(messages)
    return {"messages": [response]}


def writer_agent(
    state: AgentState, config: RunnableConfig
):  # dict yerine RunnableConfig
    api_key = config.get("configurable", {}).get("api_key")
    llm = ChatLiteLLM(model="gpt-4o", api_key=api_key)

    sys_msg = SystemMessage(
        content="""Sen ödüllü bir İçerik Yazarısın (Copywriter) ve SEO uzmanısın.
        Görevin, sohbet geçmişindeki araştırma verilerini alıp, okuyucuyu içine çeken, 
        harika alt başlıkları (H2, H3) olan, profesyonel bir blog yazısı üretmektir.
        Asla internette arama yapma, sadece sana verilen verileri kullan.
        Yazının sonuna mutlaka 'Bu içerik Otonom Yapay Zeka Sistemi tarafından hazırlanmıştır.' notunu düş."""
    )
    messages = [sys_msg] + state["messages"]

    # DİKKAT: writer_llm değil, yukarıda tanımladığımız llm'i kullanıyoruz!
    response = llm.invoke(messages)
    return {"messages": [response]}


# --- 5. YÖNLENDRİCİ (ROUTER) ---
# MİMARİ DERS: Araştırmacı işini bitirdiğinde nereye gideceğiz?
def router(state: AgentState):
    last_message = state["messages"][-1]

    # Eğer Araştırmacı "Benim internette arama yapmam lazım" dediyse (tool_calls), bandı araçlara yönlendir
    if last_message.tool_calls:
        return "tools"

    # Araştırmacı aramalarını bitirip ham veriyi sunduysa, bandı yazara (Yazar ajan) gönder!
    return "yazar"


# --- MİMARİYİ (GRAPH) İNŞA EDİYORUZ ---
# 1. Taşınma bandı tanımlaması
workflow = StateGraph(AgentState)

# 2. İşçileri yerleştir
workflow.add_node("arastirmaci", researcher_agent)
# Yeni işçimiz: LLM araç kullanmak isterse o aracı gerçekten çalıştıracak olan Node
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("yazar", writer_agent)

# 3. Rayları (Edges) ve Akıllı Şalteri döşe
workflow.add_edge(START, "arastirmaci")  # Fabrika ilk olarak Araştırmacı ile başlar

# AKILLI ŞALTER (Conditional Edge): Asistan cevap verdikten sonra kontrol et:
workflow.add_conditional_edges(
    "arastirmaci", router
)  # Araştırmacıdan sonra kararı Router'a bırak

workflow.add_edge(
    "tools", "arastirmaci"
)  # Araçlar internetten veriyi bulunca tekrar Araştırmacıya okut

workflow.add_edge(
    "yazar", END
)  # Yazar işini bitirince fabrika durur, ürün teslim edillir

# Hafıza yöneticisini başlat (Şimdilik RAM üzerinde, ileride PostgreSQL'e bağlayabiliriz )
memory = MemorySaver()

# Fabrikayı derlerken "checkpointer" olarak bu hafızayı kullanmasını söylüyoruz
app = workflow.compile(checkpointer=memory)


# --- TEST AŞAMASI (İNTERAKTİF CLI) ---
if __name__ == "__main__":
    logging.info(
        "LangGraph motoru interaktif modda başlatılıyor. Çıkmak için 'q' veya 'quit' yazın."
    )

    # MİMARİ NOT: 'thread_id', bu konuşmanın kime ait olduğunun kimliğidir.
    # Eğer thread_id="ahmet_1" yaparsan Ahmet'in hafızasını, "ayse_2" yaparsan Ayşe'nin hafızasını okur.
    config = {"configurable": {"thread_id": "benim_ilk_oturumum_1"}}

    print("\n" + "=" * 50)
    print("🤖 Baş Araştırmacı Ajan Aktif. (Çıkmak için 'q' yazın)")
    print("=" * 50 + "\n")

    while True:
        # Kullanıcıdan canlı olarak mesaj alıyoruz
        user_input = input("Sen: ")

        # Çıkış kontrolü
        if user_input.lower() in ["q", "quit", "çıkış"]:
            print("Görüşmek üzere!")
            break

        # DİKKAT: Artık eski mesajları biz göndermiyoruz! SADECE yeni mesajı veriyoruz.
        # LangGraph 'thread_id' sayesinde eski mesajları veritabanından kendisi bulup birleştirecek
        state_input = {"messages": [{"role": "user", "content": user_input}]}

        # 'config' parametresini göndererek ajanın doğru hafıza dosyasını açmasını sağlıyoruz
        final_state = app.invoke(state_input, config=config)

        # Ajanın verdiği en son cevabı ekrana basıyoruz
        ai_response = final_state["messages"][-1].content
        print(f"\nAjan: {ai_response}\n")
