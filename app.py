import streamlit as st
from interpreter import interpreter
from memoria import memoria
import sqlite3
import json
import os
import time
import warnings 
from PIL import Image
import io

warnings.filterwarnings("ignore")  
# Configuração do Interpreter
interpreter.os = True
interpreter.llm.supports_vision = True
interpreter.llm.supports_functions = True
interpreter.llm.model = "gpt-4o-mini"
interpreter.llm.api_key = os.getenv("OPENAI_API_KEY")  # Substitua pela sua chave de API
interpreter.llm.context_window = 128000
interpreter.auto_run = True
interpreter.verbose = False
interpreter.loop = True
interpreter.sync_computer = True
interpreter.system_message = memoria
#interpreter.llm.api_base = "http://192.168.1.215:1234/v1"

interpreter.conversation_history = True
interpreter.conversation_history_path = os.path.dirname(os.path.realpath(__file__))
interpreter.conversation_filename = "conversations.json"

# Inicializar histórico de conversação na sessão do Streamlit
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('conversas.db')
c = conn.cursor()

st.title("Aiden, o majestoso")

# Exibir a conversa
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(message["content"])

# Caixa de texto para entrada do usuário
user_input = st.chat_input("Digite sua mensagem")

if user_input:
    # Adicionar mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Exibir a mensagem do usuário imediatamente
    with st.chat_message("user"):
        st.markdown(user_input)

    # Placeholder para a mensagem do assistente
    with st.chat_message("assistant"):
        assistant_message_placeholder = st.empty()
        assistant_response = ""

        # Obter resposta do Interpreter
        for result in interpreter.chat(user_input, stream=True):
            if isinstance(result, dict):
                if result.get('type') == 'message':
                    if 'content' in result:
                        chunk = result['content']
                        assistant_response += chunk
                        # Atualizar o placeholder com a nova parte da resposta
                        assistant_message_placeholder.markdown(assistant_response)
                    # Ignorar mensagens de controle 'start' e 'end'
            elif isinstance(result, str):
                # Adicionar resultados que são strings diretamente
                assistant_response += result
                assistant_message_placeholder.markdown(assistant_response)
            # Opcional: Adicionar um pequeno delay para melhorar a experiência do usuário
            time.sleep(0.01)

        # Adicionar resposta do GPT ao histórico
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Salvar conversa em conversations.json
        with open('conversations.json', 'w', encoding='utf-8') as file:
            json.dump(st.session_state.messages, file, ensure_ascii=False)
            
                    # Inserir as duas últimas mensagens no banco de dados
            for item in st.session_state.messages[-2:]:  # Apenas as últimas duas mensagens
                if item.get("role") != "computer":
                    item_copy = item.copy()
                    item_copy.pop("type", None)
                    item_copy.pop("format", None)
                    json_string = json.dumps(item_copy, ensure_ascii=False)
                    c.execute("INSERT INTO finetune (conteudo) VALUES (?)", (json_string,))
            conn.commit()
# Adiciona um campo para upload de imagem
uploaded_file = st.file_uploader("Faça upload de uma imagem", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Exibir a imagem carregada
    st.image(uploaded_file, caption="Imagem carregada", use_column_width=True)

    # Verifica se o modelo suporta visão
    if interpreter.llm.supports_vision:
        # Converta o arquivo carregado para uma imagem PIL
        image_data = uploaded_file.read()
        img = Image.open(io.BytesIO(image_data))  # Converte os dados binários em uma imagem PIL
        
        with st.chat_message("assistant"):
            st.markdown("Interpretando a imagem...")

            try:
                # Envia a imagem PIL para o modelo e obtém a descrição em português
                image_description = interpreter.llm.vision_renderer(
                    lmc={"content": img, "format": "pil_image"},
                    query="Descreva esta imagem em português."
                )
                
                # Exibe a descrição gerada a partir da imagem
                st.markdown(f"Descrição da imagem: {image_description}")

                # Salva a resposta no histórico de mensagens
                st.session_state.messages.append({"role": "assistant", "content": image_description})

            except Exception as e:
                st.error(f"Erro ao processar a imagem: {str(e)}")
    else:
        st.error("O modelo não suporta a interpretação de imagens.")

    # Salvar conversa
    with open('conversations.json', 'w', encoding='utf-8') as file:
        json.dump(st.session_state.messages, file, ensure_ascii=False)

        # Inserir as duas últimas mensagens no banco de dados
        for item in st.session_state.messages[-2:]:  # Apenas as últimas duas mensagens
            if item.get("role") != "computer":
                item_copy = item.copy()
                item_copy.pop("type", None)
                item_copy.pop("format", None)
                json_string = json.dumps(item_copy, ensure_ascii=False)
                c.execute("INSERT INTO finetune (conteudo) VALUES (?)", (json_string,))
        conn.commit()

# Fechar a conexão com o banco de dados ao finalizar
conn.close()
