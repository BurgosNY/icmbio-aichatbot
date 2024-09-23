import time
from ai_helpers import *
from fasthtml.common import *
from dotenv import load_dotenv
import os
import re

load_dotenv()


tailwind_css = Link(
    rel='stylesheet', href='/static/css/output.css', type='text/css')
# Head(Title('Guia de Gestão'), tailwind_css),
headers = [tailwind_css,
           KatexMarkdownJS(),
           Link(rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
           *Socials(title="Chatbot Interface",
                    description='Learn the foundations of FastHTML',
                    site_name='about.fastht.ml',
                    image='/static/logo.png',
                    url='https://about.fastht.ml')]
app, rt = fast_app(live=True, hdrs=headers, pico=False, debug=True)


@rt("/")
def get():
    return (
        Title("Guia de Gestão - ICMBio"),
        Div(
            navbar(),
            Div(
                # Wrapper div for responsive layout
                Div(
                    # Left column (1/3 width on larger screens, full width and centered on smaller screens)
                    Div(
                        H1("Guia de Gestão - ICMBio",
                           cls="text-2xl font-bold mb-4"),
                        P("Este ChatBot é um sistema de inteligência artificial que responde a perguntas sobre processos, normas e regulação do ICMBio. Nesta versão 0.3 ele está limitado aos macroprocessos 'Autorização para licenciamento ambiental', 'Gestão do Uso Público' e 'Manejo Integrado do Fogo'.", cls="mb-4"),
                        P("A pergunta será processada por um modelo de IA, que passará por diferentes etapas: primeiro classificará a pergunta em um dos macroprocessos, depois irá refraseá-la internamente, selecionará documentos da base de dados e, só aí, fará a pergunta para um modelo mais avançado. Ele terá acesso a documentos como manuais, portarias, legislações, etc.", cls="mb-4"),
                        P("Para começar, digite sua pergunta na área de texto ao lado e clique no botão 'Enviar'. Lembre-se que quanto mais contexto e especificidade sua pergunta tiver, mais provável será que a resposta seja correta.", cls="mb-4"),
                        cls="w-full lg:w-1/3 mb-8 lg:mb-0 lg:pr-8"
                    ),
                    # Right column (2/3 width on larger screens, full width on smaller screens)
                    Div(
                        Form(
                            Textarea(placeholder="Escreva sua pergunta aqui...",
                                     cls="textarea textarea-bordered w-full", name="question"),
                            Button("Enviar", cls="btn btn-primary w-full mt-4"),
                            cls="w-full max-w-md mx-auto mb-8",
                            hx_post="/chat_start", hx_target="#chat_start",
                            hx_swap="outerHTML", hx_indicator="#loading"
                        ),
                        Div(
                            Div(cls="loading loading-spinner loading-lg"),
                            id="loading",
                            cls="htmx-indicator"
                        ),
                        Div(id="chat_start", cls="mt-8"),
                        cls="w-full lg:w-2/3"
                    ),
                    cls="flex flex-col lg:flex-row gap-6"
                ),
                cls="container mx-auto px-4 py-8 max-w-6xl"
            )
        ),
        Footer(
            "2024 - ICMBio",
            cls="footer p-8 bg-neutral text-neutral-content fixed bottom-0 left-0 right-0"
        )
    )


@rt("/chat_start")
def post(question: str):
    import time
    time.sleep(3)
    primeira_resposta = "Essa é uma resposta instintiva. Pense em *algo assim* e depois *escolha o macroprocesso*"
    resposta = "Essa é uma resposta instintiva. Pense em *algo assim* e depois *escolha o macroprocesso*"
    macro_processo = "A"
    justificativa = "Essa é uma resposta instintiva. Pense em *algo assim* e depois *escolha o macroprocesso* Vou pensar **melhor**."
    return Div(
        Div(
            Div(I(cls="fas fa-robot")),
            Div(
                "Buscando documentos sobre: ",
                Strong(nome_macroprocesso(macro_processo)),
                cls="mt-2"
            ),
            Div(f"💭 {justificativa}", cls="marked p-8 italic"),
        ),
        Div(id="chat_final", cls="mt-8"),
        Hidden(name="question", value=question),
        Hidden(name="category", value=macro_processo),
        Hidden(name="first_answer", value=justificativa),
        Div(
            Div(cls="loading loading-spinner loading-lg"),
            id="loading2",
            cls="htmx-indicator"),
        id="chat_start", cls="mt-8",
        hx_post="/chat_category",
        hx_target="#chat_final",
        hx_swap="outerHTML",
        hx_trigger="load",
        hx_include="[name='question'],[name='category'],[name='first_answer']",
        hx_indicator="#loading2"
    )


@rt("/chat_category")
def post(category: str, question: str, first_answer: str):
    mensagens = [ell.user(question), ell.system(first_answer)]
    markdown = """
# Resposta do Chatbot

Este é um exemplo de markdown com **vários recursos**. Podemos incluir:

- Listas com marcadores
- *Texto em itálico*
- [Links](https://www.example.com)
- `Código inline`

## Segundo Parágrafo

No segundo parágrafo, podemos adicionar uma tabela e uma citação:

| Coluna 1 | Coluna 2 |
|----------|----------|
| Dado 1   | Dado 2   |

> Esta é uma citação que pode conter informações importantes ou destacadas.
    """
    import time
    time.sleep(3)
    referencias = [
        {
            "nome_do_arquivo": "Manual Análise de Conformidade.pdf",
            "pagina": 4
        },
        {
            "nome_do_arquivo": "Documento 2",
            "pagina": 2
        }
    ]
    referencia_items = [
        Li(
            A(
                I(cls="fas fa-file-alt"),
                f" {ref['nome_do_arquivo']} (página {ref['pagina']})",
                href=os.environ['SUPABASE_STORAGE_URL'] +
                sanitize_filename(ref['nome_do_arquivo'])
            )
        ) for ref in referencias
    ]

    return Div(
        Div(
            Div(I(cls="fas fa-robot")),
            Div(markdown, cls="marked"),
            Div(
                P(I(cls="fas fa-file-alt"),
                  P("Documentos consultados:"), cls="mt-2"),
                Ul(
                    *referencia_items,
                    cls="list-disc list-inside"
                ),
                cls="mt-2"
            ),
        ),
        id="chat_category", cls="mt-8"
    )


# OLD CODE
@rt("/real_chat_start")
def post(question: str):
    primeira_resposta = resposta_instintiva(question)
    resposta = escolhe_macro_processo(primeira_resposta)
    macro_processo = resposta.content[0].parsed.macro_processo
    justificativa = resposta.content[0].parsed.justificativa
    return Div(
        Div(
            Div("Chatbot:", cls="font-bold"),
            Div(
                "Buscando documentos sobre: ",
                Strong(nome_macroprocesso(macro_processo)),
                cls="mt-2"
            ),
            Div(f"💭 {justificativa}", cls="marked p-8"),
        ),
        Div(id="chat_final", cls="mt-8"),
        Div(
            Div(cls="loading loading-spinner loading-lg"),
            id="loading2",
            cls="htmx-indicator"),
        Hidden(name="question", value=question),
        Hidden(name="category", value=macro_processo),
        Hidden(name="first_answer", value=justificativa),
        id="chat_start", cls="mt-8",
        hx_post="/chat_category",
        hx_target="#chat_final",
        hx_swap="outerHTML",
        hx_trigger="load",
        hx_include="[name='question'],[name='category'],[name='first_answer']",
        hx_indicator="#loading2"
    )


@rt("/real_chat_category")
def post(category: str, question: str, first_answer: str):
    mensagens = [ell.user(question), ell.system(first_answer)]
    docs = busca_documentos(mensagens, return_collection(category), 5)
    print(f'Documentos encontrados. Montando resposta...\n')
    resposta = resposta_rag(mensagens, docs['documents'])
    referencias = resposta.content[0].parsed.documentos
    markdown = resposta.content[0].parsed.resposta
    return Div(
        Div(
            Div("Chatbot:", cls="font-bold"),
            Div(markdown, cls="marked"),
        ),
        id="chat_category", cls="mt-8"
    )


# components
def navbar():
    return Div(
        Div(
            A(
                Img(src="/static/logo.png", alt="Logo", cls="w-10 h-10"),
                "ChatBot",
                cls="btn btn-ghost normal-case text-xl"
            ),
            cls="flex-1"
        ),
        Div(
            Ul(
                Li(A("Home", href="#")),
                Li(A("About", href="#")),
                Li(A("Contact", href="#")),
                cls="menu menu-horizontal px-1 hidden md:flex"
            ),
            cls="flex-none hidden md:block"
        ),
        Div(
            Div(
                Input(id="navbar-toggle", type="checkbox", cls="hidden"),
                Label(
                    Svg(
                        Path(d="M3 12h18M3 6h18M3 18h18", stroke="currentColor",
                             stroke_width="2", stroke_linecap="round", stroke_linejoin="round"),
                        cls="w-6 h-6", viewBox="0 0 24 24", fill="none", xmlns="http://www.w3.org/2000/svg"
                    ),
                    for_="navbar-toggle",
                    cls="btn btn-square btn-ghost md:hidden"
                ),
                cls="dropdown"
            ),
            Ul(
                Li(A("Sobre", href="#")),
                Li(A("Banco de Respostas", href="#")),
                Li(A("Contato", href="#")),
                cls="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52",
                tabindex="0"
            ),
            cls="dropdown dropdown-end md:hidden"
        ),
        cls="navbar bg-base-100")

# Helpers


def sanitize_filename(filename):
    name, ext = os.path.splitext(filename)
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    return f"{safe_name}{ext}"


serve()
