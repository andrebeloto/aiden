"""
Text -> Knowledge Graph
1. text -> cypher

Constraints:
- Use the existing schema before creating new nodes and relationships.
"""
import os
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
import dspy
from src.neo4j import Neo4j
from openai import OpenAI
from flask import Flask, request, jsonify
from dspy.retrieve import retrieve
from collections import OrderedDict

app = Flask(__name__)

# set up Neo4j using NEO4J_URI
neo4j = Neo4j(uri=os.getenv("NEO4J_URI"), user=os.getenv("NEO4J_USER"), password=os.getenv("NEO4J_PASSWORD"))
client = OpenAI(api_key="API-KEY")
lm = dspy.OpenAI(
    model="gpt-4o-mini",
    max_tokens=1024,
)
dspy.configure(lm=lm)

def gerar_embeddings(text):
    embeddings_response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text,
        encoding_format="float",
        dimensions=1024
    )
    return embeddings_response.data[0].embedding

class CypherFromText(dspy.Signature):
    """
    Diretivas Gerais:
    Entender o Texto:
        Analise o texto para identificar entidades principais e suas ações.
        Determine contextos temporais, locacionais e descrições relevantes.
    Categorização de Nós:
        Use categorias específicas para os nós com base no tipo de entidade. Por exemplo, use Servidor, Dispositivo, Usuário para tecnologia ou Animal, Localização, Objeto para narrativas mais genéricas.
        Atribua subcategorias sempre que possível para refinar a especificidade (ex: Animal pode ser subdividido em Mamífero, Réptil, etc.).
    Especificação de Relacionamentos:
        Identifique claramente as ações como tipos de relacionamentos. Evite generalizações como acao; prefira moveu_para, observou, interagiu_com.
        Descreva a natureza da relação com precisão, distinguindo ações físicas, visuais, ou contextuais.
    Propriedades dos Nós e Relacionamentos:
        Inclua as propriedades name e text em todos os nós e relacionamentos. O name deve ser uma descrição concisa, enquanto text deve refletir o contexto completo associado à entidade ou ação.
        Considere adicionar propriedades como tipo, data, status para fornecer mais contextos e facilitar consultas específicas.
    Instruções de Formatação:
        Todas as declarações Cypher devem ser em português do Brasil, em minúsculas e sem acentuação.
        Assegure-se de que os nomes dos nós e relacionamentos estejam coerentes com o esquema existente do Neo4j.
    Exemplo de Processamento de Texto para Cypher:
    Texto: "O técnico atualizou o servidor principal durante a noite para melhorar a performance."
    Análise: Identifique técnico como Usuário, servidor principal como Servidor, e noite como Tempo.
    Estratégia Refinada para Propriedades de Texto
    Textos Descritivos Específicos:
        Nós: Para cada nó, a propriedade text deve incluir uma descrição que capte a essência e os detalhes específicos da entidade. Por exemplo, em vez de repetir o texto completo do evento em cada nó, descreva o nó com base em suas características únicas ou no papel que desempenha no contexto da informação fornecida.
        Relacionamentos: Para os relacionamentos, a propriedade text deve refletir a ação ou interação específica entre os nós. Isso ajuda a distinguir diferentes tipos de ações e suas nuances no contexto geral do texto.
    Exemplo Prático
    Se considerarmos o exemplo anterior, onde "O técnico atualizou o servidor principal durante a noite para melhorar a performance", poderíamos ajustar as propriedades text da seguinte maneira:
    Nós:
        Técnico: "Técnico responsável pela manutenção e atualização de sistemas."
        Servidor Principal: "Servidor principal que desempenha funções críticas na rede e requer atualizações frequentes para otimização."
        Noite: "Período fora do horário comercial, ideal para manutenções que requerem menos interrupção das operações diárias."
    Relacionamentos:
        Atualizou: "Ação de atualização realizada pelo técnico para melhorar a performance do servidor."
        Durante: "Relacionamento temporal indicando que a ação ocorreu durante a noite."
    Uso Universal do MERGE: Utilize o comando MERGE para lidar tanto com a inserção de novos nós quanto com a atualização de nós existentes de forma segura e eficiente. Especifique claramente que o MERGE deve ser seguido por configurações SET que aplicam tanto para a criação de novos itens (nós ou relacionamentos) quanto para a atualização de itens existentes.
    Configuração de Propriedades:
        Ao Usar MERGE: Inclua sempre um SET imediatamente após o MERGE para definir ou atualizar as propriedades. Isso garante que as propriedades sejam configuradas corretamente independentemente de o nó ser novo ou já existente.
        Propriedades Padrão para Todos os Casos: Configure o comando para que, após o MERGE, as propriedades sejam ajustadas automaticamente, aplicando alterações que sejam apropriadas tanto para situações de criação quanto para atualização.
    Exemplo de Comando Cypher:
        Considerando o texto exemplo "O técnico atualizou o servidor principal durante a noite para melhorar a performance.": 
        
    MERGE (u:Usuario {name: 'tecnico'})
    SET u.text = 'Técnico responsável pela manutenção e atualização de sistemas.'
    MERGE (s:Servidor {name: 'servidor principal'})
    SET s.text = 'Servidor principal que desempenha funções críticas na rede.'
    MERGE (t:Tempo {name: 'noite'})
    SET t.text = 'Período fora do horário comercial.'
    MERGE (u)-[r:ATUALIZOU]->(s)
    SET r.text = 'Atualização para melhorar a performance.'
    MERGE (u)-[d:DURANTE]->(t)
    SET d.text = 'Ação realizada durante a noite.' 

    Instruções de Implementação:
    Ao criar comandos Cypher, concentre-se na precisão das conexões e na riqueza dos detalhes, assegurando que o grafo final seja uma representação fidedigna e útil das memórias e informações.
    E POR ULTIMO, SOMENTE RETORNE O COMANDO CYPHER, SEM NECESSIDADE DE EXPLICAÇÕES.
    """

    text = dspy.InputField(desc="Texto para modelar usando nós, propriedades e relacionamentos.")
    neo4j_schema = dspy.InputField(desc="Esquema do gráfico atual no Neo4j como uma lista de NÓS e RELACIONAMENTOS.")
    statement = dspy.OutputField(desc="Declaração Cypher em português do Brasil, minúsculo e sem acentuação para mesclar nós e relacionamentos encontrados no texto, não explique nada, apenas retorne o comando")

generate_cypher = dspy.ChainOfThought(CypherFromText)

def pesquisar_grafo_embedding(embedding_pergunta):
    query = """
    MATCH (c)
    WITH c, gds.similarity.cosine(c.embedding, $embedding_pergunta) AS similaridade
    WHERE similaridade > 0.5
    RETURN c.name
    ORDER BY similaridade desc
    LIMIT 1
    """
    parametros = {'embedding_pergunta': embedding_pergunta}
    resultado = neo4j.query(query, parameters=parametros)

        # Acessa o nome diretamente, assumindo que há pelo menos um resultado
    if resultado:
        nome = resultado[0]['c.name']  # Acessa o primeiro item da lista e a chave 'c.name'
        return nome
    else:
        return None  # Retorna None se não houver resultados

    # Retornar lista de conceitos relacionados
    #return [(registro["name"],registro["conceito"], registro["similaridade"]) for registro in resultados]

def pesquisar_relacoes(texto):
    query= """
    MATCH (n {name: $texto})- [r] - (relacoes) 
    RETURN TYPE(r) + ': ' +relacoes.name as resultado
    """
    parametros = {'texto': texto}
    resultados = neo4j.query(query, parameters=parametros)
    
    # Acessa o nome diretamente, assumindo que há pelo menos um resultado
    nomes = [resultado['resultado'] for resultado in resultados]
    return nomes

def atualizar_embeddings():
    # Atualiza embeddings para nós
    nodos_sem_embedding = neo4j.query("""
        MATCH (n)
        WHERE n.embedding IS NULL
        RETURN id(n) AS node_id, n.text AS text
    """)
    for nodo in nodos_sem_embedding:
        embedding = gerar_embeddings(nodo['text'])
        neo4j.query("MATCH (n) WHERE id(n) = $node_id SET n.embedding = $embedding",
                    parameters={"node_id": nodo['node_id'], "embedding": embedding})

    # Atualiza embeddings para relacionamentos
    rels_sem_embedding = neo4j.query("""
        MATCH ()-[r]->()
        WHERE r.embedding IS NULL
        RETURN id(r) AS relationship_id, r.text AS text
    """)
    for rel in rels_sem_embedding:
        embedding = gerar_embeddings(rel['text'])
        neo4j.query("MATCH ()-[r]->() WHERE id(r) = $relationship_id SET r.embedding = $embedding",
                    parameters={"relationship_id": rel['relationship_id'], "embedding": embedding})


@app.route('/add', methods=['POST'])
def add():
    try:
        data = request.json
        question = data.get('text', '').replace("\n", " ")
        if not question:
            raise ValueError("Texto vazio não é permitido.")

        cypher = generate_cypher(text=question, neo4j_schema=neo4j.fmt_schema())
        neo4j.query(cypher.statement.replace('```', ''))

        atualizar_embeddings()  # Chamada da função centralizada
        return jsonify({'status': 'Success', 'message': 'Dados adicionados e embeddings atualizados!'}), 200
    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400


@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question', '').strip()

    if not question or question.lower() == 'exit':
        return jsonify({'response': 'Goodbye!'}), 200

    embedding_pergunta = gerar_embeddings(question)
    resultados = pesquisar_grafo_embedding(embedding_pergunta)
    print(resultados)
    resultado = pesquisar_relacoes(resultados)
    print(resultado)

    return jsonify(resultado), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

    
