import json

import httpx
import pytest

from estudos.agente.modelo import Chamada, ErroModelo, Gemini, ModeloFalso, Texto, Turno, Uso

FERRAMENTAS = [{"name": "buscar", "description": "busca na matéria", "parameters": {"type": "object", "properties": {}}}]


def _sse(*eventos: dict) -> bytes:
    return "".join(f"data: {json.dumps(e)}\r\n\r\n" for e in eventos).encode()


def _gemini(resposta: httpx.Response | Exception, pedidos: list) -> Gemini:
    def tratar(request: httpx.Request) -> httpx.Response:
        pedidos.append(request)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    return Gemini("CHAVE-SECRETA", "gemini-teste", 30, transporte=httpx.MockTransport(tratar))


def test_gemini_monta_a_requisicao():
    pedidos = []
    g = _gemini(httpx.Response(200, content=_sse({"candidates": [{"content": {"parts": [{"text": "oi"}]}}]})), pedidos)
    turnos = [Turno("usuario", "me ajude"),
              Turno("modelo", None, [Chamada("buscar", {"consulta": "polares"}, "assin-1")]),
              Turno("ferramenta", resultados=[("buscar", {"trechos": []})])]
    list(g.responder("você é o tutor", turnos, FERRAMENTAS))
    [req] = pedidos
    assert "streamGenerateContent" in str(req.url) and "alt=sse" in str(req.url) and "CHAVE" not in str(req.url)
    assert req.headers["x-goog-api-key"] == "CHAVE-SECRETA"
    corpo = json.loads(req.content)
    assert corpo["systemInstruction"]["parts"][0]["text"] == "você é o tutor"
    assert corpo["tools"] == [{"functionDeclarations": FERRAMENTAS}]
    papeis = [c["role"] for c in corpo["contents"]]
    assert papeis == ["user", "model", "user"]
    chamada = corpo["contents"][1]["parts"][0]
    assert chamada["functionCall"] == {"name": "buscar", "args": {"consulta": "polares"}} and chamada["thoughtSignature"] == "assin-1"
    assert corpo["contents"][2]["parts"][0]["functionResponse"] == {"name": "buscar", "response": {"trechos": []}}


def test_gemini_le_texto_chamada_e_uso_do_sse():
    pedidos = []
    g = _gemini(httpx.Response(200, content=_sse(
        {"candidates": [{"content": {"parts": [{"text": "Vou "}]}}]},
        {"candidates": [{"content": {"parts": [{"text": "buscar."}]}}]},
        {"candidates": [{"content": {"parts": [{"functionCall": {"name": "buscar", "args": {"consulta": "x"}},
                                                 "thoughtSignature": "s9"}]}}],
         "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 30}},
    )), pedidos)
    eventos = list(g.responder("s", [Turno("usuario", "oi")], FERRAMENTAS))
    assert eventos == [Texto("Vou "), Texto("buscar."), Chamada("buscar", {"consulta": "x"}, "s9"), Uso(120, 30)]


@pytest.mark.parametrize("resposta, motivo", [
    (httpx.Response(400, json={"error": {"message": "API key not valid. Please pass a valid API key.",
                                         "details": [{"reason": "API_KEY_INVALID"}]}}), "chave_invalida"),
    # revisão final: 400 sem ser de chave (pedido grande demais, esquema de ferramenta recusado) não é chave inválida
    (httpx.Response(400, json={"error": {"message": "Invalid JSON payload received.", "status": "INVALID_ARGUMENT"}}),
     "pedido_invalido"),
    (httpx.Response(401, json={"error": {"message": "unauthenticated"}}), "chave_invalida"),
    (httpx.Response(403, json={"error": {"message": "forbidden"}}), "chave_invalida"),
    (httpx.Response(429, json={"error": {"message": "quota"}}), "limite_de_uso"),
    (httpx.Response(503, json={"error": {"message": "overloaded"}}), "indisponivel"),
    (httpx.ReadTimeout("lento"), "tempo_esgotado"),
    (httpx.ConnectError("sem rede"), "indisponivel"),
])
def test_gemini_erros_viram_motivo(resposta, motivo):
    with pytest.raises(ErroModelo) as erro:
        list(_gemini(resposta, []).responder("s", [Turno("usuario", "oi")], FERRAMENTAS))
    assert erro.value.motivo == motivo


def test_modelo_falso_roteiriza_rodadas():
    falso = ModeloFalso([[Texto("a"), Chamada("buscar", {}), Uso(1, 2)], [ErroModelo("indisponivel")]])
    assert list(falso.responder("s", [Turno("usuario", "1")], [])) == [Texto("a"), Chamada("buscar", {}), Uso(1, 2)]
    with pytest.raises(ErroModelo):
        list(falso.responder("s", [Turno("usuario", "2")], []))
    assert len(falso.pedidos) == 2 and falso.pedidos[0][1][0].texto == "1"


class _CaiNoMeio(httpx.SyncByteStream):
    def __iter__(self):
        yield _sse({"candidates": [{"content": {"parts": [{"text": "Com"}]}}],
                    "usageMetadata": {"promptTokenCount": 500, "candidatesTokenCount": 40}})
        raise httpx.ReadError("conexão caiu")


def test_queda_no_meio_leva_o_uso_ja_recebido():
    g = _gemini(httpx.Response(200, stream=_CaiNoMeio()), [])
    with pytest.raises(ErroModelo) as erro:
        list(g.responder("s", [Turno("usuario", "oi")], FERRAMENTAS))
    assert erro.value.motivo == "indisponivel" and erro.value.uso == Uso(500, 40)


def test_sse_malformado_vira_erro_do_modelo():
    g = _gemini(httpx.Response(200, content=b"data: {nao e json\r\n\r\n"), [])
    with pytest.raises(ErroModelo):
        list(g.responder("s", [Turno("usuario", "oi")], FERRAMENTAS))
