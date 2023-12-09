from fastapi import (
 APIRouter,
 Depends,
 Form,
 HTTPException,
 Path,
 Request,
 status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.Usuario import Usuario
from repositories.UsuarioRepo import UsuarioRepo
from util.mensagem import redirecionar_com_mensagem
from util.seguranca import *
from util.validator import add_error, is_matching_fields, is_not_empty, is_password
router = APIRouter(prefix="/usuario")
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def get_index(
   request: Request,
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
 
   usuarios = UsuarioRepo.obter_todos()
   return templates.TemplateResponse(
   "usuario/index.html",
   {"request": request, "usuario": usuario, "usuarios": usuarios},
   )

@router.get("/excluir/{id_usuario:int}", response_class=HTMLResponse)
async def get_excluir(
   request: Request,
   id_usuario: int = Path(),
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   usuario_excluir = UsuarioRepo.obter_por_id(id_usuario)
   return templates.TemplateResponse(
   "usuario/excluir.html",
   {"request": request, "usuario": usuario, "usuario_excluir":
   usuario_excluir},
   )

@router.post("/excluir/{id_usuario:int}", response_class=HTMLResponse)
async def post_excluir(
   usuario: Usuario = Depends(obter_usuario_logado),
   id_usuario: int = Path(),
   ):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   
   if id_usuario == 1:
      response = redirecionar_com_mensagem(
      "/usuario",
      "Não é possível excluir o administrador padrão do sistema.",
      )
      return response

   if id_usuario == usuario.id:
      response = redirecionar_com_mensagem(
      "/usuario",
      "Não é possível excluir o próprio usuário que está logado.",
      )
      return response
 
   UsuarioRepo.excluir(id_usuario)
   response = redirecionar_com_mensagem(
   "/usuario",
   "Usuário excluído com sucesso.",
   )
   return response

@router.get("/alterar/{id_usuario:int}", response_class=HTMLResponse)
async def get_alterar(
   request: Request,
   id_usuario: int = Path(),
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

   usuario_alterar = UsuarioRepo.obter_por_id(id_usuario)
   return templates.TemplateResponse(
   "usuario/alterar.html",
   {"request": request, "usuario": usuario, "usuario_alterar":
   usuario_alterar},
      )

@router.post("/alterar/{id_usuario:int}", response_class=HTMLResponse)
async def post_alterar(
   id_usuario: int = Path(),
   nome: str = Form(...),
   email: str = Form(...),
   administrador: bool = Form(False),
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   if id_usuario == 1:
      response = redirecionar_com_mensagem(
      "/usuario",
      "Não é possível alterar dados do administrador padrão.",
      )
      return response

   UsuarioRepo.alterar(
   Usuario(id=id_usuario, nome=nome, email=email, admin=administrador)
   )
   response = redirecionar_com_mensagem(
   "/usuario",
   "Usuário alterado com sucesso.",
   )
   return response

@router.get("/arearestrita", response_class=HTMLResponse)
async def get_index(
   request: Request,
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
 
   usuarios = UsuarioRepo.obter_todos()
   return templates.TemplateResponse(
   "usuario/arearestrita.html",
   {"request": request, "usuario": usuario, "usuarios": usuarios},
   )


from fastapi import Depends

@router.post("/alterardados")
async def post_alterar(
    nome: str = Form(...),
    email: str = Form(...),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Crie uma instância de Usuario com o ID do usuário logado
    usuario_a_alterar = Usuario(id=usuario.id, nome=nome, email=email)

    # Chame o método alterar do UsuarioRepo passando a instância criada
    UsuarioRepo.alterar(usuario_a_alterar)

    response = redirecionar_com_mensagem("/usuario/arearestrita", "Usuário alterado com sucesso!")
    return response

@router.post("/alterarsenha", response_class=HTMLResponse)
async def postAlterarSenha(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    senha_atual: str = Form(""),
    nova_senha: str = Form(""),
    conf_nova_senha: str = Form(""),
):
    # normalização dos dados
    senha_atual = senha_atual.strip()
    nova_senha = nova_senha.strip()
    conf_nova_senha = conf_nova_senha.strip()

    # verificação de erros
    erros = {}

    # validação do campo senha_atual
    is_not_empty(senha_atual, "senha_atual", erros)
    is_password(senha_atual, "senha_atual", erros)

    # validação do campo nova_senha
    is_not_empty(nova_senha, "nova_senha", erros)
    is_password(nova_senha, "nova_senha", erros)

    # validação do campo conf_nova_senha
    is_not_empty(conf_nova_senha, "conf_nova_senha", erros)
    is_matching_fields(conf_nova_senha, "conf_nova_senha", nova_senha, "Nova Senha",
                       erros)

    # só verifica a senha no banco de dados se não houverem erros de validação
    if len(erros) == 0:
        hash_senha_bd = UsuarioRepo.obter_senha_por_email(usuario.email)
        if hash_senha_bd:
            if not conferir_senha(senha_atual, hash_senha_bd):
                add_error("senha_atual", "Senha atual está incorreta.", erros)

    # se tem erro, mostra o formulário novamente
    if len(erros) > 0:
        valores = {}
        return templates.TemplateResponse(
            "root/login.html",
            {
                "request": request,
                "usuario": usuario,
                "erros": erros,
                "valores": valores,
            },
        )

    # se passou pelas validações, altera a senha no banco de dados
    hash_nova_senha = obter_hash_senha(nova_senha)
    if usuario:
        UsuarioRepo.alterarSenha(usuario.id, hash_nova_senha)

    response = redirecionar_com_mensagem("/usuario/arearestrita", "Senha alterada com sucesso!")
    return response