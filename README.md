# Aiden - Assistente Inteligente com Base em Conhecimento

## Visão Geral
Aiden é um assistente inteligente desenvolvido em Python que utiliza inteligência artificial e tecnologias como GPT (OpenAI), Neo4j e Streamlit para oferecer uma interface interativa e avançada para armazenamento, consulta e interpretação de informações estruturadas como grafos semânticos.

## Tecnologias Utilizadas
- **Python**
- **Flask**: Framework para criação de APIs REST.
- **Streamlit**: Interface gráfica web interativa.
- **Neo4j**: Banco de dados orientado a grafos.
- **GPT-4 (OpenAI)**: Modelos para interpretação semântica e geração de embeddings.
- **SQLite**: Armazenamento local de histórico das conversas.

## Funcionalidades
- **Armazenamento Inteligente**: Captura e estrutura informações em grafos com Neo4j.
- **Consulta Semântica**: Usa embeddings para realizar consultas com base em similaridade.
- **Interação Conversacional**: Interface intuitiva para interação em linguagem natural.
- **Processamento de Imagens**: Interpretação de imagens por IA com descrição automática em português.
- **Histórico e Treinamento**: Registro de interações para treinamento e melhoria contínua do modelo.

## Estrutura do Projeto

```bash
├── app.py               # Interface Streamlit
├── embedder.py          # Conversão de texto para grafo de conhecimento
├── memoria.py           # Instruções detalhadas para interação com API
├── .env                 # Configurações e variáveis de ambiente
└── conversas.db         # Banco SQLite com histórico das conversas
```

## Configuração do Ambiente

### Instalação
Clone o repositório e instale as dependências:
```bash
git clone https://github.com/andrebeloto/aiden.git
cd aiden
pip install -r requirements.txt
```

### Configuração de Ambiente
Crie um arquivo `.env` com:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=seu_usuario
NEO4J_PASSWORD=sua_senha
OPENAI_API_KEY=sua_chave_openai
```

### Execução

Inicie o servidor Flask:
```bash
python embedder.py
```

Inicie a interface Streamlit:
```bash
streamlit run app.py
```

## Uso
- Acesse a interface via `http://localhost:8501` para interagir com o assistente Aiden.
- Utilize comandos `/add` para adicionar informações e `/query` para consultar dados.

## Licença
Este projeto está licenciado sob a licença MIT.

---

Desenvolvido por [André Beloto](https://github.com/andrebeloto).

