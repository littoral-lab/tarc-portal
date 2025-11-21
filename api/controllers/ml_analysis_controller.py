import logging

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from schemas.ml_analysis import MLAnalysisRequest, MLAnalysisResponse
from services.ml_analysis_service import MLAnalysisService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ml-analysis"])


@router.post("/ml/analyze", response_model=MLAnalysisResponse)
def analyze_data(
    request: MLAnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Realiza análise de Machine Learning nos dados de sensores.

    Tipos de análise disponíveis:
    - clustering: Agrupa dados em clusters similares
    - prediction: Prediz valores futuros
    - classification: Classifica dados em categorias (baixo/normal/alto)

    Campos disponíveis:
    - temperature: Temperatura
    - rssi: Sinal RSSI (se disponível)
    - vazao: Vazão/Fluxo
    """
    logger.info(
        f"📊 Iniciando análise ML - Tipo: {request.analysis_type.value}, "
        f"Campo: {request.target_field.value}, Período: {request.time_range}"
    )

    try:
        # Executar análise
        logger.info("🔄 Executando análise...")
        results = MLAnalysisService.perform_analysis(
            db=db,
            analysis_type=request.analysis_type.value,
            target_field=request.target_field.value,
            time_range=request.time_range,
        )

        # Verificar se houve erro
        if "error" in results:
            logger.error(f"❌ Erro na análise: {results['error']}")
            raise HTTPException(status_code=400, detail=results["error"])

        # Preparar resposta
        from datetime import datetime

        metadata = {
            "dataset": request.dataset,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info("✅ Análise concluída com sucesso")

        return MLAnalysisResponse(
            analysis_type=request.analysis_type.value,
            target_field=request.target_field.value,
            time_range=request.time_range,
            results=results,
            metadata=metadata,
            message="Análise concluída com sucesso",
        )
    except HTTPException as e:
        logger.error(f"❌ HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"❌ Erro inesperado ao realizar análise: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao realizar análise: {str(e)}"
        )
