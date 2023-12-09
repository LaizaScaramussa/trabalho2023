from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from models.Usuario import Usuario
from repositories.ProdutoRepo import ProdutoRepo
from repositories.UsuarioRepo import UsuarioRepo
from util.mensagem import adicionar_cookie_mensagem, redirecionar_com_mensagem
from util.seguranca import adicionar_cookie_autenticacao, conferir_senha, excluir_cookie_autenticacao, gerar_token, obter_usuario_logado
from util.templateFilters import capitalizar_nome_proprio, formatarIdParaImagem
from util.validator import *
from util.seguranca import *

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.on_event("startup")
async def startup_event():
   templates.env.filters["id_img"] = formatarIdParaImagem

@router.get("/")
async def get_index(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
):
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)   
    produtos = ProdutoRepo.obter_todos()
    return templates.TemplateResponse(
        "root/index.html",
        {"request": request, "usuario": usuario, "produtos": produtos},
    )


@router.get("/login", response_class=HTMLResponse)
async def get_login(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
):
    return templates.TemplateResponse(
        "root/login.html",
        {"request": request, "usuario": usuario},
    )


@router.post("/login", response_class=RedirectResponse)
async def post_login(
    email: str = Form(...),
    senha: str = Form(...),
    return_url: str = Query("/"),
):
    hash_senha_bd = UsuarioRepo.obter_senha_por_email(email)

    # Verifica se a senha está correta
    if conferir_senha(senha, hash_senha_bd):
        token = gerar_token()
        UsuarioRepo.alterar_token_por_email(token, email)
        response = RedirectResponse(return_url, status.HTTP_302_FOUND)
        adicionar_cookie_autenticacao(response, token)
        adicionar_cookie_mensagem(response, "Login realizado com sucesso.")
    else:
        response = redirecionar_com_mensagem(
            "/login",
            "Credenciais inválidas. Tente novamente.",
        )
    return response


@router.get("/logout")
async def get_logout(usuario: Usuario = Depends(obter_usuario_logado)):
    if usuario:
        UsuarioRepo.alterar_token_por_email("", usuario.email)
        response = RedirectResponse("/", status.HTTP_302_FOUND)
        excluir_cookie_autenticacao(response)
        adicionar_cookie_mensagem(response, "Saída realizada com sucesso.")
    return response

@router.get("/criarConta", response_class=HTMLResponse)
async def get_criarConta(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
):
    return templates.TemplateResponse(
        "root/criarConta.html",
        {"request": request, "usuario": usuario},
    )

@router.post("/criarConta")
async def postUsuario(request: Request,
                    usuario: Usuario = Depends(obter_usuario_logado),
                    nome: str = Form(),
                    email: str = Form(),
                    senha: str = Form(),
                    confsenha: str = Form(),
                    admin: Optional[bool] = Form(None),
                    token: Optional[str] = Form("")):
                      
  # normalização dos dados
  nome = capitalizar_nome_proprio(nome).strip()
  email = email.lower().strip()
  senha = senha.strip()
  confsenha = confsenha.strip()

  # verificação de erros
  erros = {}
  # validação do campo nome
  is_not_empty(nome, "nome", erros)
  is_person_fullname(nome, "nome", erros)
  # validação do campo email
  is_not_empty(email, "email", erros)
  # validação do campo senha
  is_not_empty(senha, "senha", erros)
  is_password(senha, "senha", erros)
  # validação do campo confSenha
  is_not_empty(confsenha, "confSenha", erros)
  is_matching_fields(confsenha, "confSenha", senha, "Senha", erros)
  # validação do campo id

  # se tem erro, mostra o formulário novamente
  if len(erros) > 0:
    valores = {}
    valores["nome"] = nome
    valores["email"] = email.lower()
    return templates.TemplateResponse(
      "root/criarConta.html",
      {
        "request": request,
        "usuario": usuario,
        "erros": erros,
        "valores": valores,
      },
    )
# Exemplo de conversão para inteiro antes de criar um objeto Usuario

  usuario = UsuarioRepo.inserir(
  Usuario(id=0, nome=nome, email=email, senha=obter_hash_senha(senha)
         ))
  response = redirecionar_com_mensagem("/login", "Sua conta foi criada com sucesso! Use seu e-mail e senha para fazer login!")
  return response