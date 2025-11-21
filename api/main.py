import logging

from controllers.chirpstack_controller import router as chirpstack_router
from controllers.device_controller import router as device_router
from controllers.ml_analysis_controller import router as ml_analysis_router
from controllers.packet_controller import router as packet_router
from database import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Cria as tabelas no banco de dados (apenas para desenvolvimento)
# Em produção, use Alembic para gerenciar migrações
Base.metadata.create_all(bind=engine)
logger.info("🚀 TARC API iniciada")

app = FastAPI(title="TARC API", version="1.0.0")

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substituir por URLs específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(packet_router)
app.include_router(device_router)
app.include_router(chirpstack_router)
app.include_router(ml_analysis_router)


@app.get("/")
def read_root():
    return {"Hello": "World", "version": "1.0.0"}
