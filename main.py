from datetime import datetime
import time
import uuid
from ell import Message
from ai_helpers import *
from fasthtml.common import *
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import re

load_dotenv()


tailwind_css = Link(
    rel='stylesheet', href='/static/css/output.css', type='text/css')
hyperscript_css = Script(
    src='https://unpkg.com/hyperscript.org@0.9.12', type='text/javascript')
# Head(Title('Guia de Gestão'), tailwind_css),
headers = [tailwind_css,
           hyperscript_css,
           KatexMarkdownJS(),
           Link(rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
           *Socials(title="Chatbot Interface",
                    description='Learn the foundations of FastHTML',
                    site_name='about.fastht.ml',
                    image='/static/logo.png',
                    url='https://about.fastht.ml')]
app, rt = fast_app(live=True, hdrs=headers, pico=False, debug=True)
db = MongoClient(os.environ['MONGODB_URI'])
collection = db['icmbio']['chatbot_responses']
suggestions = db['icmbio']['suggestions']
feedback = db['icmbio']['feedback']


@rt("/")
def get(session):
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    return (
        Title("Guia de Gestão - ICMBio"),
        Div(
            navbar(),
            Div(
                # Wrapper div for responsive layout
                Div(
                    # Left column (unchanged)
                    Div(
                        Dialog("Este é um dialog"),
                        H1("Sobre este guia",
                           cls="text-xl font-bold mb-4"),
                        P("Este ChatBot é um sistema de inteligência artificial que responde a perguntas sobre processos, normas e regulação do ICMBio. Nesta versão 0.3 ele está limitado aos macroprocessos 'Autorização para licenciamento ambiental', 'Gestão do Uso Público' e 'Manejo Integrado do Fogo'."),
                        P("A pergunta será processada por um modelo de IA, que passará por diferentes etapas: primeiro classificará a pergunta em um dos macroprocessos, depois irá refraseá-la internamente, selecionará documentos da base de dados e, só aí, fará a pergunta para um modelo mais avançado. Ele terá acesso a documentos como manuais, portarias, legislações, etc."),
                        P("Para começar, digite sua pergunta na área de texto ao lado e clique no botão 'Enviar'. Lembre-se que quanto mais contexto e especificidade sua pergunta tiver, mais provável será que a resposta seja correta. Depois dessa interação, avalie usando o botão abaixo."),
                        modal_rate(session),
                        Div(id="dialog"),
                        cls="w-full lg:w-1/3 mb-8 lg:mb-0 lg:pr-8"
                    ),

                    # Right column (modified)
                    Div(
                        Div(
                            Div(id="chat-history",
                                cls="overflow-y-auto flex-grow"),
                            Div(
                                Form(
                                    Textarea(placeholder="Escreva sua pergunta aqui...",
                                             cls="textarea textarea-bordered w-full", name="question"),
                                    Button(
                                        Div(cls="loading loading-spinner loading-lg htmx-indicator", id='loading'),
                                        "Enviar", cls="btn bg-olive-green hover:bg-forest-green w-full mt-2"),
                                    Hidden(name="is_follow_up", value="false"),
                                    cls="w-full",
                                    hx_post="/chat_router", hx_target="#chat-history",
                                    hx_swap="beforeend", hx_indicator="#loading"
                                ),
                                cls="border-t pt-4 bg-base-200 p-4"
                            ),
                            cls="flex flex-col h-full"
                        ),
                        cls="w-full lg:w-2/3 border border-base-300 rounded-lg overflow-hidden flex flex-col"
                    ),
                    cls="flex flex-col lg:flex-row gap-6 h-[calc(100vh-100px)]"
                ),
                cls="container mx-auto px-4 py-8 max-w-6xl h-full"
            ),
            cls="flex flex-col h-screen"
        ),
        Script("""
            document.body.addEventListener('htmx:afterOnLoad', function(event) {
                var chatHistory = document.getElementById('chat-history');
                chatHistory.scrollTop = chatHistory.scrollHeight;
            });
        """)
    )


@rt("/chat_router")
def post(question: str, is_follow_up: str, session):
    if is_follow_up == "false":
        return chat_start(session, question)
    else:
        return chat(session, question)


@rt("/chat_start")
def chat_start(session, question: str):
    # Existing chat_start logic
    macro_selector = escolhe_macro_processo(question)
    process = macro_selector.content[0].parsed.macro_processo
    reason = macro_selector.content[0].parsed.justificativa

    return Div(
        Div(
            chat_bubble(
                "bot", f"Buscando documentos sobre: **{nome_macroprocesso(process)}**"),
            chat_bubble("bot", f"💭 {reason}"),
        ),
        Hidden(name="question", value=question),
        Hidden(name="category", value=process),
        Hidden(name="first_answer", value=reason),
        hx_post="/chat",
        hx_target="#chat-history",
        hx_swap="beforeend",
        hx_indicator="#loading",
        hx_trigger="load",
        hx_include="[name='question'],[name='category'],[name='first_answer']",
    )


@rt("/chat")
def chat(session, question: str, category: str = None, first_answer: str = None):
    # If category and first_answer are provided, it's the first question
    if category and first_answer:
        tentative_answer = resposta_instintiva(question)
        collection.insert_one({
            'question': question,
            'category': category,
            'messages': [
                {'role': 'user', 'content': question},
                {'role': 'assistant', 'content': tentative_answer}
            ],
            'created_at': datetime.now(),
            'session_id': session['session_id']
        })
        # Process the question using the category and first_answer
        processed_answer = process_question(question, category, [{"role": "user", "content": question},
                                                                 {"role": "assistant", "content": tentative_answer}], tentative_answer)
        print(processed_answer)
    else:
        obj = collection.find_one({'session_id': session['session_id']})
        processed_answer = process_question(
            question, obj['category'], obj['messages'])
        collection.update_one({'session_id': session['session_id']},
                              {'$push': {'messages': {'$each': [
                                  {'role': 'user', 'content': question},
                                  {'role': 'assistant', 'content': processed_answer}]}}})

    return Div(
        chat_bubble("user", question),
        chat_bubble("bot", processed_answer['answer']),
        doc_bubble(processed_answer['references']),
        Script(
            "document.querySelector('input[name=is_follow_up]').value = 'true';"),
        cls="border-t pt-4"
    )


# Evaluate modal
# This function is called when the user clicks on the "Avaliar resposta" button
# It opens a modal with a rating form and a comment field
def modal_rate(session):
    return Div(
        Button("Avalie esta interação", cls="btn btn-success",
               onclick="my_modal_2.showModal()"),
        Dialog(
            Form(
                H3("Ajude-nos a melhorar", cls="text-lg font-bold"),
                P("A sua opinião será salva junto com a conversa para que possamos entender e aprimorar o chatbot."),
                P("Em uma escala de 1 a 5 estrelas, como você avalia a resposta do chatbot?"),
                Div(
                    Div(
                        Input(type="radio", name="rating", value=1,
                              cls="mask mask-star-2 bg-orange-400"),
                        Input(type="radio", name="rating", value=2,
                              cls="mask mask-star-2 bg-orange-400"),
                        Input(type="radio", name="rating", value=3,
                              cls="mask mask-star-2 bg-orange-400", checked="checked"),
                        Input(type="radio", name="rating", value=4,
                              cls="mask mask-star-2 bg-orange-400"),
                        Input(type="radio", name="rating", value=5,
                              cls="mask mask-star-2 bg-orange-400"),
                    ),
                    cls="rating"
                ),
                Div(
                    Textarea(name="impressions", placeholder="Suas impressões gerais...",
                             cls="textarea textarea-bordered w-full", id="autoResizeTextarea"),
                    cls="py-6"),
                Button("Enviar feedback", type="submit",
                       cls="btn btn-primary w-full"),
                Script("""
const textarea = document.getElementById('autoResizeTextarea');
textarea.addEventListener('input', function() {
this.style.height = 'auto';
this.style.height = (this.scrollHeight) + 'px';});
"""),
                cls="modal-box",
                method="post",
                action="/process_feedback"
            ),
            Form(
                Button("close"),
                method="dialog", cls="modal-backdrop"
            ),
            id="my_modal_2", cls="modal"
        )
    )


@rt("/process_feedback")
def process_feedback(rating: int, impressions: str, session):
    feedback.insert_one({
        'rating': rating,
        'impressions': impressions,
        'created_at': datetime.now(),
        'session_id': session['session_id']
    })
    print(f"Received feedback - Rating: {rating}, Impressions: {impressions}")
    return RedirectResponse(url="/", status_code=303)


def process_question(question, category=None, messages=None, first_answer=None):
    if category and first_answer:
        mensagens = [ell.user(question), ell.system(first_answer)]
        docs = busca_documentos(mensagens, return_collection(category), 3)
        resposta = resposta_rag(mensagens, docs)
        referencias = resposta.content[0].parsed.documentos
        refs = [{'link': sanitize_filename(
            ref.nome_do_arquivo), 'p': ref.pagina, 'arquivo': ref.nome_do_arquivo} for ref in referencias]
        markdown = resposta.content[0].parsed.resposta
        return {"answer": markdown, "references": refs}
    else:
        # for testing purposes
        messages = [Message(role=message['role'], content=message['content'])
                    for message in messages]
        messages.append(Message(role="user", content=question))
        response = chat_history(messages, temperature=0.2)
        print(response)

        return {"answer": response, "references": []}

# components


def navbar():
    return Div(
        Div(
            A(
                Div(
                    Img(src="/static/img/icmbio-logo-header.png",
                        alt="Logo", cls="h-10"),
                    cls="mr-3"
                ),
                Div(
                    "Guia de Gestão",
                    cls="text-2xl font-semibold px-4"
                ),
                href="/",
                cls="flex items-center text-black"
            ),
            cls="flex-1 flex items-center"
        ),
        Div(
            Ul(
                Li(A("Perguntas anteriores", href="/perguntas", cls="text-black")),
                Li(A("Contato", href="/contato", cls="text-black")),
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
                Li(A("Banco de Respostas", href="#", cls="text-black")),
                Li(A("Contato", href="#", cls="text-black")),
                cls="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52",
                tabindex="0"
            ),
            cls="dropdown dropdown-end md:hidden"
        ),
        cls="navbar bg-base-100 p-4")


def chat_bubble(sender, message):
    is_bot = sender == "bot"
    avatar_src = "static/img/onca.jpeg" if is_bot else "static/img/human-icon.png"
    chat_class = "chat-start" if is_bot else "chat-end"
    bubble_class = "bg-slate-300 text-black" if is_bot else "bg-olive-green text-black"
    return Div(
        Div(
            Div(
                Div(
                    Img(
                        alt=f"{'Bot' if is_bot else 'User'} avatar",
                        src=avatar_src
                    ),
                    cls="w-10 rounded-full"
                ),
                cls="chat-image avatar"
            ),
            Div(message, cls=f"chat-bubble {bubble_class} marked"),
            cls=f"chat {chat_class} px-2 py-4"
        )
    )


def doc_bubble(docs):
    storage = os.environ['SUPABASE_STORAGE_URL']
    chat_class = "chat-start"
    bubble_class = "bg-slate-300 text-black"

    if not docs:
        content = P("Nenhum documento consultado: usando memória interna")
    else:
        content = Div(
            P("Documentos consultados:"),
            Ul(
                *[Li(
                    A(
                        I(cls="fas fa-file-alt"),
                        f" {ref['arquivo']} (página {ref['p']})",
                        href=f"{storage}{ref['link']}#page={ref['p']}",
                        target="_blank",
                        rel="noopener noreferrer",
                        cls="text-blue-600 hover:text-blue-800 underline hover:underline-offset-2"
                    )
                ) for ref in docs],
                cls="list-disc list-inside"
            )
        )

    return Div(
        Div(
            Div(
                Div(
                    Img(
                        alt="Bot",
                        src="static/img/onca.jpeg"
                    ),
                    cls="w-10 rounded-full"
                ),
                cls="chat-image avatar"
            ),
            Div(content, cls=f"chat-bubble {bubble_class}"),
            cls=f"chat {chat_class} px-2 py-4"
        )
    )
# Outras páginas


@ rt("/contato")
def get():
    return (
        Title("Contato - ICMBio Guia de Gestão"),
        Div(
            navbar(),
            Div(
                Div(
                    Div("""
Este site é desenvolvido pela [Co.Inteligência](https://cointeligencia.ai/),
com o financiamento da [Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH](https://www.giz.de/en/worldwide/12055.html).

Se você tem dúvidas, sugestões ou achou algum bug, entre em contato pelo formulário:
                      """, cls="marked"),
                    Form(
                        Div(
                            Input(type="text", name="nome",
                                  placeholder="Seu nome", cls="input input-bordered w-full"),
                            Input(type="email", name="email",
                                  placeholder="Email", cls="input input-bordered w-full"),
                            cls="grid grid-cols-2 gap-4 py-4"
                        ),
                        Textarea(name="mensagem", placeholder="Mensagem",
                                 cls="textarea textarea-bordered w-full mb-4", rows="4"),
                        Div(
                            Button("Enviar", type="submit",
                                   cls="btn btn-primary w-full"),
                            cls="flex justify-center"
                        ),
                        method="post", action="/contato"
                    ),
                    cls="max-w-2xl mx-auto p-6 bg-base-100 shadow-xl rounded-lg"
                ),
                cls="container mx-auto px-4 py-8 flex justify-center items-center min-h-[calc(100vh-64px)]"
            ),
            cls="flex flex-col min-h-screen"
        )
    )


@ rt("/contato")
def post(nome: str, email: str, mensagem: str):
    suggestions.insert_one({
        'nome': nome,
        'email': email,
        'mensagem': mensagem,
        'created_at': datetime.now()
    })
    return (
        Title("Contato - ICMBio Guia de Gestão"),
        Div(
            navbar(),
            Div(
                Titled("Obrigado pelo contato!",
                       P(f"""
Recebemos sua mensagem e responderemos em breve no email {email}.
"""),
                       A("Voltar para a página inicial",
                           href="/", cls="btn bg-sea-green hover:bg-forest-green mt-4")
                       ),
                cls="container mx-auto px-4 py-8 flex justify-center items-center min-h-[calc(100vh-64px)]"
            ),
        )
    )


@ rt("/perguntas")
def get():
    return (
        Title("Perguntas feitas - ICMBio Guia de Gestão"),
        Div(
            navbar(),
            Div(
                Div(
                    H2("Em Breve: Histórico de perguntas",
                        cls="text-2xl font-bold mb-4"),
                    cls="max-w-2xl mx-auto p-6 bg-base-100 shadow-xl rounded-lg"
                ),
                cls="container mx-auto px-4 py-8 flex justify-center items-center min-h-[calc(100vh-64px)]"
            ),
            cls="flex flex-col min-h-screen"
        )
    )


# Helpers
def sanitize_filename(filename):
    name, ext = os.path.splitext(filename)
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    return f"{safe_name}{ext}"


serve()
