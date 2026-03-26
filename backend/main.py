import os
import logging
import litellm
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_litellm import ChatLiteLLM
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Arama motoru objesi (max 3 sonuç)
search_engine = DuckDuckGoSearchResults(max_results=3)


# @tool dekoratörü, altındaki Python fonksiyonunu LLM'in anlayacağı bir "Araç-Tool"a çevirir
@tool
def web_search(query: str):
    """
    İnternette güncel bilgi aramak için kullanılır.
    Bilmediğin, güncel olan veya emin olmadığın her bilgi için bu aracı kullanmalısın.
    """
    return search_engine.run(query)


# Sistemdeki tüm araçlarımızı bir listeye koy
tools = [web_search]

# LLM'imizi tanımlıyoruz ve '.bind_tools' ile beynine bu araçları yerleştiriyoruz.
llm = ChatLiteLLM(model="gpt-4o").bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def ask_agent(state: AgentState):
    try:
        # Ajanın anayasası (System Prompt)
        sys_msg = SystemMessage(
            content="""
        Sen dünya çapında saygı gören, acımasız ama çok zeki bir Baş Araştırmacı (Lead Researcher) yapay zekasın. Kullanıcıya asla 'merhaba, nasıl yardımcı olabilirim' gibi ucuz asistan lafları etme. 
        Cevaplarını her zaman çok profesyonel, net ve veriye dayalı olarak ver. 
        Eğer internetten bir bilgi bulduysan, cevabının sonuna mutlaka '[Kaynak: İnternet Taraması]' ibaresini ekle.
        """
        )

        messages = [sys_msg] + state["messages"]

        # LLM artık araçları biliyor ve kendi format çevirisini kendi yapıyor
        response = llm.invoke(messages)
        return {"messages": [response]}

        """
         Eski sürüm, litellm ile modele mesaj gönder gelen cevabı LangGraph ile State'e ekle
        response = litellm.completion(model="openai/gpt-4o", messages=messages)

        ai_response_content = response.choices[0].message.content
        return {"messages": [{"role": "assistant", "content": ai_response_content}]}
        """

    except Exception as e:
        logging.error(f"LLM çağrısı sırasında hata: {e}")


# 1. Taşınma bandı tanımlaması
workflow = StateGraph(AgentState)

# 2. İşçileri yerleştir
workflow.add_node("asistan_node", ask_agent)
# Yeni işçimiz: LLM araç kullanmak isterse o aracı gerçekten çalıştıracak olan Node
workflow.add_node("tools", ToolNode(tools))

# 3. Rayları (Edges) ve Akıllı Şalteri döşe
workflow.add_edge(START, "asistan_node")

# AKILLI ŞALTER (Conditional Edge): Asistan cevap verdikten sonra kontrol et:
# - Eğer araç kullanmak istediyse bandı "tools" düğümüne kaydır.
# - Sadece metin cevap verdiyse END'e (çıkışa) yönlendir.
workflow.add_conditional_edges("asistan_node", tools_condition)

# DÖNGÜ (Loop): Araç işini bitirip internetten veriyi bulunca, bunu okuması için bandı tekrar asistana geri yolla!
workflow.add_edge("tools", "asistan_node")

# Hafıza yöneticisini başlat (Şimdilik RAM üzerinde, ileride PostgreSQL'e bağlayabiliriz )
memory = MemorySaver()

# Fabrikayı derlerken "checkpointer" olarak bu hafızayı kullanmasını söylüyoruz
app = workflow.compile(checkpointer=memory)

"""
Eski kod: State tanımla, nodeları ve edgeleri yerleştir mesaj gönder, gelen cevabı State'e ekle
# --- MİMARİYİ (GRAPH) İNŞA EDİYORUZ ---

# 1. Taşıma bandını (State) tanımlıyoruz
workflow = StateGraph(AgentState)

# 2. İşçimizi (Node) fabrikaya yerleştiriyoruz
# (Birinci parametre işçinin adı, ikinci parametre çalıştıracağı fonksiyon)
workflow.add_node("asistan_node", ask_agent)

# 3. Rayları (Edges) döşüyoruz
workflow.add_edge(START, "asistan_node")  # Başlangıçtan direkt asistana git
workflow.add_edge("asistan_node", END)  # Asistan işini bitirince çıkışa git

# 4. Grafiği derliyoruz (Compile) - Bu adım planı çalıştırılabilir bir uygulamaya çevirir
app = workflow.compile()
"""


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

"""
Eski kod: Arama yapabilen agent -> LLM -> terminal
# --- TEST AŞAMASI ---
if __name__ == "__main__":
    # Sisteme ilk girecek malzemeyi (kullanıcı mesajını) hazırlıyoruz
    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": "Yapay zeka otonom ajanlarının (autonomous agents) geleceği hakkında bana kısa ve çok net bir vizyon sun.",
            }
        ]
    }

    logging.info("LangGraph motoru çalıştırılıyor...")

    logging.info(f"Aracın Adı: {web_search.name}")
    logging.info(f"Aracın Açıklaması: {web_search.description}")

    # app.invoke() tüm sistemi başlatır, START'tan girip END'den çıkana kadar çalışır ve son durumu (state) döner
    final_state = app.invoke(initial_state)

    # Sepetteki (State) en son mesajı, yani LLM'in cevabını ekrana basıyoruz
    logging.info(f"Ajanın Cevabı: {final_state['messages'][-1].content}")
"""
