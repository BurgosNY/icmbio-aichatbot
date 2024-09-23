from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings
from pinecone_langchain_forked import PineconeVectorStore
from dotenv import load_dotenv
import ell
import os

load_dotenv()


# Classes
class EscolheMacroProcesso(BaseModel):
    macro_processo: str
    justificativa: str


class DocumentoRAG(BaseModel):
    nome_do_arquivo: str
    pagina: int


class RespostaRAG(BaseModel):
    resposta: str
    documentos: list[DocumentoRAG]


# Funções do LLM
@ell.simple(model="gpt-4o-mini")
def resposta_instintiva(pergunta: str):
    """Você é um assistente virtual do Instituto Chico Mendes de Conservação da Biodiversidade (ICMBio). 
    Sua tarefa é responder às perguntas dos usuários relacionadas aos processos de gestão do Instituto, incluindo licenciamento ambiental, 
    manejo integrado do fogo, uso público das unidades de conservação e outros temas afins. Fornecer respostas claras e objetivas, 
    assegurando que estejam alinhadas com o escopo e as diretrizes do ICMBio. Evite fugir do asunto.
    Suas respostas serão utilizadas posteriormente para busca em documentos. Utilize as palavras-chave necessárias para a tarefa.
    Sua resposta deve ser em markdown.
    """
    return f"Responda à pergunta: {pergunta}."


@ell.complex(model="gpt-4o-mini", response_format=EscolheMacroProcesso)
def escolhe_macro_processo(pergunta: str) -> EscolheMacroProcesso:
    """Você é um assistente virtual do Instituto Chico Mendes de Conservação da Biodiversidade (ICMBio). 
    Sua tarefa é escolher o macro processo mais adequado para responder à pergunta do usuário.
    """
    return f"""Analise esta pergunta:  {pergunta}

Agora avalie a descrição de diferentes macroprocessos no ICMBIO:

macroprocesso 1 - "Autorização para Licenciamento Ambiental":

Este processo envolve as etapas e procedimentos para o ICMBio emitir pareceres, autorizações e manifestações dentro do licenciamento ambiental, especialmente quando empreendimentos podem impactar Unidades de Conservação (UC) federais. Aqui, são abordadas questões como:

- Fases de elaboração de documentos técnicos, como o Termo de Referência;

- Tipos de manifestações e licenças ambientais emitidas;

- Critérios legais e normativos que obrigam a participação do ICMBio;

- Análise de compatibilidade dos empreendimentos com as UCs afetadas;

- Procedimentos técnicos do Protocolo de Avaliação de Impactos Ambientais.

macroprocesso 2 - "Gestão do Uso Público"

Abrange a organização, planejamento e autorização de atividades de visitação em unidades de conservação federais. Este macroprocesso é gerido pela Coordenação Geral de Uso Público e Negócios (CGEUP), composta por três setores principais: COEST, CONCES e DOVIS.

Aqui são tratadas questões relacionadas principalmente a:

- Planejamento de visitas e infraestrutura física em unidades de conservação, como trilhas e áreas de uso público.

- Sinalização em áreas de visitação, incluindo tipos de placas, materiais utilizados, segurança e padronização.

- Concessões de serviços e atividades turísticas, como contratos para exploração de áreas, definição de valores de ingressos e serviços.

- Autorização de eventos e serviços de apoio à visitação em áreas protegidas.

- Diversificação de oportunidades de recreação e desenvolvimento sustentável dentro das unidades de conservação.

- Manutenção e monitoramento de atividades de uso público, como gestão de contratos de concessões e análise de impactos sobre as áreas visitadas.

macroprocesso 3 - "Manejo Integrado do Fogo"

"Manejo Integrado do Fogo" (MIF) se refere ao uso controlado, planejado e adaptativo do fogo em Unidades de Conservação, visando a conservação, prevenção de incêndios e o uso sustentável do território. Este macroprocesso envolve o manejo do fogo como uma ferramenta para alcançar objetivos específicos de conservação e para minimizar os impactos negativos do fogo.

As perguntas relacionadas a este macroprocesso podem tratar de:

- Princípios do Manejo Integrado do Fogo, que incluem o uso do fogo como ferramenta ecológica e técnica, considerando os aspectos culturais e sociais.

- Planejamento do MIF, que aborda a conservação, manutenção e recuperação dos ecossistemas por meio do uso controlado do fogo.

- Conceitos de ecossistemas relacionados ao fogo, como ecossistemas sensíveis, dependentes e influenciados pelo fogo.

- Técnicas de controle e combate de incêndios florestais, incluindo medidas de prevenção, combate e queima prescrita.

- Queima controlada e queima prescrita, que são técnicas aplicadas de forma planejada para o manejo de vegetação e redução de incêndios.

- Aspectos ecológicos e técnicos do manejo do fogo, como "regime do fogo", "janela de queima" e "incêndio".

- Participação social e envolvimento de comunidades tradicionais na gestão do fogo, integrando saberes tradicionais com conhecimentos técnicos e científicos.

- Perguntas sobre MIF relacionadas a unidades de conservação específicas.

Agora relacione a pergunta ao macroprocesso e escolha somente uma dessas opções.

A) macroprocesso 1 - "Autorização para Licenciamento Ambiental"

B) macroprocesso 2 - "Gestão do Uso Público"

C) macroprocesso 3 - "Manejo Integrado do Fogo"

D) a pergunta não se relaciona aos macroprocessos inseridos na base de dados da IA.

A resposta deve ser no formato JSON, com as chaves:

- macro_processo: letra que representa a opção escolhida
- justificativa: justificativa concisa para a escolha
    """


@ell.simple(model="gpt-4o-mini")
def sumariza_para_vetor(resposta: str):
    return f"""Você é um especialista do Instituto Chico Mendes de Conservação da Biodiversidade (ICMBio).
    Você deve sumarizar respostas, com o objetivo de facilitar a busca por documentos relevantes em uma base vetorizada.
    Sumarize a resposta: {resposta}"""


@ell.complex(model="gpt-4o-2024-08-06", response_format=RespostaRAG)
def resposta_rag(mensagens: list, documentos: list) -> RespostaRAG:
    """Você é um assistente virtual do Instituto Chico Mendes de Conservação da Biodiversidade (ICMBio). 
    Sua tarefa é responder à pergunta do usuário com base no seu conhecimento, referenciando os documentos encontrados para suporte e verificação.
    """
    return f"""
Considere esta pergunta:  {mensagens[0]}

Agora responda a pergunta, usando como referência os seguintes documentos:

{parse_documents(documentos)}

Sua resposta deve ser clara e contemplar de forma abrangente a pergunta. Se não souber a resposta ou algum detalhe, responda que não foi possível encontrar os detalhes nos documentos.
Ao referenciar os documentos, cite apenas o nome do documento e a página entre parênteses. Não use links ou notas de rodapé.
Sua resposta deve ser no formato JSON, com as chaves:

- resposta: resposta para a pergunta, em markdown
- documentos: lista de documentos que forneceram suporte à resposta, com nome do arquivo e página
"""


# Langchain Stuff
def initialize_vector_store(documents: int, collection: str):
    # Initialize a LangChain object for retrieving information from Pinecone.
    knowledge = PineconeVectorStore.from_existing_index(
        index_name=collection,  # default "icmbiogestao1"
        embedding=OpenAIEmbeddings()
    )
    return knowledge.as_retriever(search_kwargs={"k": documents})


# Helper function to return the collection name based on the macroprocesso
def return_collection(option: str):
    collections = {
        "A": "icmbiogestao1",
        "B": "icmbiogestao2",
        "C": "icmbiogestao3"
    }
    return collections.get(option, "icmbiogestao1")


def nome_macroprocesso(option: str):
    macroprocessos = {
        "A": "Autorização para licenciamento ambiental",
        "B": "Gestão do Uso Público",
        "C": "Manejo Integrado do Fogo",
    }
    return macroprocessos.get(option, "Não foi possível identificar o macroprocesso.")


def parse_documents(documents: list):
    data = ""
    for document in documents:
        data += f"\n\n**Arquivo**: {document.metadata['filename']}\n"
        data += f"**Página**: {document.metadata['page_number']}\n"
        data += f"**Fragmento**: {document.page_content}\n\n"
    return data


def busca_documentos(mensagens: list, macroprocesso: str, documentos: int):
    base_documentos = initialize_vector_store(
        collection=macroprocesso, documents=documentos)
    query_busca = sumariza_para_vetor(
        mensagens[-1])  # A primeira resposta da IA
    retriever = initialize_vector_store(
        documents=5, collection=macroprocesso)
    documents = retriever.invoke(query_busca)
    return {'documents': documents}
