from contextlib import closing
from datetime import date

from fastapi import APIRouter, Depends

from estudos import resumo
from estudos.api.deps import obter_settings
from estudos.api.esquemas import MateriaCriar
from estudos.api.respostas import MateriaApagada, MateriaCriada, ResumoMateria
from estudos.config import Settings
from estudos.db.conexao import conectar
from estudos.erros import Conflito
from estudos.rag.indexador import sincronizando
from estudos.repos import materia
from estudos.workspace import abrir_materia, criar_materia, descobrir_materias, mover_para_lixeira

router = APIRouter(prefix="/api/materias", tags=["matérias"])


@router.get("")
def listar(settings: Settings = Depends(obter_settings)) -> list[ResumoMateria]:
    """Cada matéria com o resumo dos cartões da tela inicial (abre e fecha o banco de cada uma)."""
    hoje = date.today()
    saida = []
    for m in descobrir_materias(settings.workspace):
        with closing(conectar(m.db)) as con:
            saida.append({
                "uid": m.uid, "nome": m.nome, "periodo": materia.obter(con).periodo,
                "unidades": resumo.total_unidades(con), "proxima_prova": resumo.proxima_prova(con, hoje),
                "importacoes_pendentes": resumo.importacoes_pendentes(con),
            })
    return saida


@router.post("", status_code=201)
def criar(corpo: MateriaCriar, settings: Settings = Depends(obter_settings)) -> MateriaCriada:
    ref = criar_materia(settings.workspace, corpo.nome, corpo.periodo)
    return {"uid": ref.uid, "nome": ref.nome}


@router.delete("/{uid}")
def apagar(uid: str, settings: Settings = Depends(obter_settings)) -> MateriaApagada:
    if sincronizando(abrir_materia(settings.workspace, uid).pasta):  # a thread de indexação escreve dentro da pasta
        raise Conflito("A matéria ainda está sendo indexada para a busca. Espere terminar e tente de novo.")
    return {"movida_para": mover_para_lixeira(settings.workspace, uid).as_posix()}
