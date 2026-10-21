from fastapi import APIRouter, Depends

from estudos.api.deps import obter_settings
from estudos.api.esquemas import MateriaCriar
from estudos.config import Settings
from estudos.workspace import criar_materia, descobrir_materias

router = APIRouter(prefix="/api/materias", tags=["matérias"])


@router.get("")
def listar(settings: Settings = Depends(obter_settings)) -> list[dict]:
    return [{"uid": m.uid, "nome": m.nome} for m in descobrir_materias(settings.workspace)]


@router.post("", status_code=201)
def criar(corpo: MateriaCriar, settings: Settings = Depends(obter_settings)) -> dict:
    ref = criar_materia(settings.workspace, corpo.nome, corpo.periodo)
    return {"uid": ref.uid, "nome": ref.nome}
