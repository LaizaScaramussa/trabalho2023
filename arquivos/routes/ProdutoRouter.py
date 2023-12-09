from io import BytesIO
from fastapi import (
 APIRouter,
 Depends,
 File,
 Form,
 HTTPException,
 Path,
 Request,
 UploadFile,
 status,
)
from fastapi.templating import Jinja2Templates
from models.Produto import Produto
from models.Usuario import Usuario
from repositories.ProdutoRepo import ProdutoRepo
from util.imagem import transformar_em_quadrada
from util.mensagem import redirecionar_com_mensagem
from util.seguranca import obter_usuario_logado
from PIL import Image
from util.templateFilters import formatarIdParaImagem


router = APIRouter(prefix="/produto")
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
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   produtos = ProdutoRepo.obter_todos()
   return templates.TemplateResponse("produto/index.html", {"request": request, "usuario": usuario, "produtos": produtos})

@router.get("/produto")
async def get_produto(
   request: Request,
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   produtos = ProdutoRepo.obter_todos()
   return templates.TemplateResponse("produto/produto.html", {"request": request, "usuario": usuario, "produtos": produtos})

@router.get("/inserir")
async def get_inserir(
   request: Request,
   usuario: Usuario = Depends(obter_usuario_logado),
   ):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   return templates.TemplateResponse(
   "produto/inserir.html",
   {"request": request, "usuario": usuario},
   )

@router.post("/inserir")
async def post_inserir(
   nome: str = Form(...),
   preco: float = Form(...),
   descricao: str = Form(...),
   arquivoImagem: UploadFile = File(),
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   produto = Produto(nome=nome, preco=preco, descricao=descricao)
   produto = ProdutoRepo.inserir(produto)
   if arquivoImagem.filename:
      conteudo_arquivo = await arquivoImagem.read()
      imagem = Image.open(BytesIO(conteudo_arquivo))
      imagem_quadrada = transformar_em_quadrada(imagem)
      imagem_quadrada.save(f"static/img/produtos/{produto.id:04d}.jpg", "JPEG")
      response = redirecionar_com_mensagem("/produto", "Produto inserido com sucesso!")
      return response
 
@router.get("/excluir/{id_produto:int}")
async def get_excluir(
   request: Request,
   id_produto: int = Path(),
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   
   produto = ProdutoRepo.obter_por_id(id_produto)
   return templates.TemplateResponse(
"produto/excluir.html",
{"request": request, "usuario": usuario, "produto": produto},
)

@router.get("/alterar/{id_produto:int}")
async def get_alterar(
   request: Request,
   id_produto: int = Path(),
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   produto = ProdutoRepo.obter_por_id(id_produto)
   return templates.TemplateResponse(
   "produto/alterar.html",
   {"request": request, "usuario": usuario, "produto": produto},
   )

@router.post("/alterar/{id_produto:int}")
async def post_alterar(
   id_produto: int = Path(),
   nome: str = Form(...),
   preco: float = Form(...),
   descricao: str = Form(...),
   arquivoImagem: UploadFile = File(),
   usuario: Usuario = Depends(obter_usuario_logado),
):
   if not usuario:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
   if not usuario.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
   ProdutoRepo.alterar(Produto(id_produto, nome, preco, descricao))
   if arquivoImagem.filename:
      conteudo_arquivo = await arquivoImagem.read()
      imagem = Image.open(BytesIO(conteudo_arquivo))
      imagem_quadrada = transformar_em_quadrada(imagem)
      imagem_quadrada.save(f"static/img/produtos/{id_produto:04d}.jpg",
      "JPEG")
   response = redirecionar_com_mensagem("/produto", "Produto alterado comsucesso!")
   return response


@router.get("/descricao/{id_produto:int}")
async def get_alterar(
    request: Request,
    id_produto: int = Path(),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if not usuario.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    produto = ProdutoRepo.obter_por_id(id_produto)
    # Crie uma lista de produtos com um único elemento
    produtos = [produto]

    return templates.TemplateResponse(
        "produto/descricao.html",
        {"request": request, "usuario": usuario, "produtos": produtos},
    )