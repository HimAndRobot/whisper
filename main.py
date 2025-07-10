from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import tempfile
import os
import logging
from typing import Optional, List
import uvicorn
from pydantic import BaseModel, Field
from config import config

# Configurar logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Faster-Whisper API",
    description="""
    ## API para transcrição de áudio usando faster-whisper
    
    Esta API permite transcrever arquivos de áudio em texto usando o modelo Whisper.
    
    ### Funcionalidades:
    - **Transcrição individual**: Transcreva um arquivo de áudio
    - **Transcrição em lote**: Transcreva múltiplos arquivos de uma vez
    - **Detecção automática de idioma**: Detecta automaticamente o idioma do áudio
    - **Timestamps**: Opção para incluir timestamps de palavras
    - **Filtro VAD**: Remove automaticamente silêncios
    
    ### Formatos suportados:
    MP3, WAV, M4A, OGG, FLAC, AAC
    """,
    version="1.0.0",
    contact={
        "name": "Suporte API",
        "url": "https://github.com/seu-usuario/whisper",
        "email": "suporte@exemplo.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carregar modelo globalmente
logger.info(f"Carregando modelo Whisper: {config.WHISPER_MODEL}")
logger.info(f"Device: {config.WHISPER_DEVICE}, Compute Type: {config.WHISPER_COMPUTE_TYPE}")

# Validar configuração
validation = config.validate_config()
if not validation["valid"]:
    logger.error("Configuração inválida:")
    for issue in validation["issues"]:
        logger.error(f"  - {issue}")
    raise SystemExit(1)

model = WhisperModel(
    config.WHISPER_MODEL, 
    device=config.WHISPER_DEVICE, 
    compute_type=config.WHISPER_COMPUTE_TYPE
)
logger.info("Modelo carregado com sucesso!")

class TranscriptionResponse(BaseModel):
    text: str = Field(..., description="Texto transcrito completo")
    language: str = Field(..., description="Idioma detectado (código ISO)")
    language_probability: float = Field(..., description="Probabilidade do idioma detectado")
    segments: List[dict] = Field(..., description="Lista de segmentos com timestamps")

class TranscriptionOptions(BaseModel):
    beam_size: Optional[int] = Field(5, description="Tamanho do beam para busca")
    language: Optional[str] = Field(None, description="Idioma do áudio (código ISO)")
    word_timestamps: Optional[bool] = Field(False, description="Incluir timestamps de palavras")
    vad_filter: Optional[bool] = Field(True, description="Usar filtro VAD para remover silêncio")

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {"message": "Faster-Whisper API está funcionando!"}

@app.get("/health")
async def health_check():
    """Verificar saúde da API"""
    model_info = config.get_model_info()
    return {
        "status": "healthy",
        "model": config.WHISPER_MODEL,
        "device": config.WHISPER_DEVICE,
        "compute_type": config.WHISPER_COMPUTE_TYPE,
        "model_info": model_info,
        "max_file_size_mb": config.MAX_FILE_SIZE // (1024 * 1024),
        "threads": config.OMP_NUM_THREADS,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    beam_size: int = 5,
    language: Optional[str] = None,
    word_timestamps: bool = False,
    vad_filter: bool = True
):
    """
    Transcrever áudio para texto
    
    - **file**: Arquivo de áudio (MP3, WAV, M4A, OGG, FLAC, AAC)
    - **beam_size**: Tamanho do beam para busca (padrão: 5)
    - **language**: Idioma do áudio (auto-detectado se não especificado)
    - **word_timestamps**: Incluir timestamps de palavras
    - **vad_filter**: Usar filtro VAD para remover silêncio
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    # Verificar extensão do arquivo
    allowed_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Formato de arquivo não suportado. Formatos aceitos: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Transcrevendo arquivo: {file.filename}")
        
        # Realizar transcrição
        segments, info = model.transcribe(
            temp_file_path,
            beam_size=beam_size,
            language=language,
            word_timestamps=word_timestamps,
            vad_filter=vad_filter
        )
        
        # Converter segments para lista
        segments_list = []
        full_text = ""
        
        for segment in segments:
            segment_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            }
            
            if word_timestamps:
                segment_dict["words"] = [
                    {
                        "start": word.start,
                        "end": word.end,
                        "word": word.word,
                        "probability": word.probability
                    }
                    for word in segment.words
                ]
            
            segments_list.append(segment_dict)
            full_text += segment.text
        
        # Limpar arquivo temporário
        os.unlink(temp_file_path)
        
        logger.info(f"Transcrição concluída. Idioma detectado: {info.language}")
        
        return TranscriptionResponse(
            text=full_text.strip(),
            language=info.language,
            language_probability=info.language_probability,
            segments=segments_list
        )
        
    except Exception as e:
        # Limpar arquivo temporário em caso de erro
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        logger.error(f"Erro na transcrição: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {str(e)}")

@app.post("/transcribe-batch")
async def transcribe_batch(files: List[UploadFile] = File(...)):
    """
    Transcrever múltiplos arquivos de áudio
    
    Transcreve vários arquivos de áudio em uma única requisição.
    """
    results = []
    
    for file in files:
        try:
            # Reutilizar a lógica do endpoint individual
            result = await transcribe_audio(file)
            results.append({
                "filename": file.filename,
                "success": True,
                "transcription": result
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {"results": results}

if __name__ == "__main__":
    # Configurar threads antes de executar
    os.environ["OMP_NUM_THREADS"] = str(config.OMP_NUM_THREADS)
    
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=getattr(config, 'RELOAD', False),
        log_level=config.LOG_LEVEL.lower()
    ) 