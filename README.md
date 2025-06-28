# Faster-Whisper API

Uma API REST para transcrição de áudio usando [faster-whisper](https://github.com/SYSTRAN/faster-whisper), otimizada para CPU com suporte a Docker.

## 🚀 Características

- ⚡ **Rápido**: Até 4x mais rápido que o Whisper original
- 🖥️ **Otimizado para CPU**: Configurado com quantização INT8
- 🔊 **Múltiplos formatos**: MP3, WAV, M4A, OGG, FLAC, AAC
- 📝 **Word timestamps**: Suporte a timestamps de palavras
- 🎯 **VAD Filter**: Filtro de detecção de atividade vocal
- 🐳 **Docker**: Deploy fácil com Docker e Docker Compose
- 📚 **Documentação automática**: Swagger UI integrado

## 📋 Pré-requisitos

- Python 3.11+
- Docker (opcional, mas recomendado)
- FFmpeg (para processamento de áudio)

## 🛠️ Instalação

### Usando Docker (Recomendado)

1. **Clone/baixe os arquivos**:
```bash
git clone <seu-repositorio>
cd whisper-api
```

2. **Execute com Docker Compose**:
```bash
docker-compose up --build
```

3. **Acesse a API**:
   - API: http://localhost:8000
   - Documentação: http://localhost:8000/docs

### Instalação Local

1. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

2. **Execute a aplicação**:
```bash
python main.py
```

## 📖 Uso da API

### Endpoints Disponíveis

- `GET /` - Status da API
- `GET /health` - Health check
- `POST /transcribe` - Transcrever um arquivo de áudio
- `POST /transcribe-batch` - Transcrever múltiplos arquivos

### Exemplos de Uso

#### 1. Transcrição Simples

```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@audio.mp3"
```

#### 2. Com Parâmetros Personalizados

```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@audio.wav" \
     -F "language=pt" \
     -F "word_timestamps=true" \
     -F "beam_size=10"
```

#### 3. Usando Python

```python
import requests

# Transcrição simples
with open("audio.mp3", "rb") as audio_file:
    response = requests.post(
        "http://localhost:8000/transcribe",
        files={"file": audio_file}
    )
    result = response.json()
    print(result["text"])

# Com parâmetros personalizados
with open("audio.wav", "rb") as audio_file:
    response = requests.post(
        "http://localhost:8000/transcribe",
        files={"file": audio_file},
        data={
            "language": "pt",
            "word_timestamps": True,
            "beam_size": 10
        }
    )
    result = response.json()
    
    # Texto completo
    print("Texto:", result["text"])
    
    # Segmentos com timestamps
    for segment in result["segments"]:
        print(f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")
```

#### 4. Usando JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function transcribeAudio(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('language', 'pt');
    form.append('word_timestamps', 'true');
    
    try {
        const response = await axios.post('http://localhost:8000/transcribe', form, {
            headers: form.getHeaders()
        });
        
        console.log('Texto:', response.data.text);
        console.log('Idioma:', response.data.language);
        
        return response.data;
    } catch (error) {
        console.error('Erro:', error.response?.data || error.message);
    }
}

// Uso
transcribeAudio('audio.mp3');
```

### Parâmetros da API

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|---------|-----------|
| `file` | arquivo | - | Arquivo de áudio (obrigatório) |
| `beam_size` | int | 5 | Tamanho do beam search |
| `language` | string | auto | Código do idioma (pt, en, es, etc.) |
| `word_timestamps` | bool | false | Incluir timestamps de palavras |
| `vad_filter` | bool | true | Filtrar silêncios com VAD |

### Resposta da API

```json
{
    "text": "Texto transcrito completo",
    "language": "pt",
    "language_probability": 0.95,
    "segments": [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "Primeiro segmento",
            "words": [
                {
                    "start": 0.0,
                    "end": 0.5,
                    "word": "Primeiro",
                    "probability": 0.98
                }
            ]
        }
    ]
}
```

## ⚙️ Configuração

### Variáveis de Ambiente

Você pode configurar a API usando variáveis de ambiente:

```bash
# Número de threads para CPU
export OMP_NUM_THREADS=4

# Modelo a ser usado (base, small, medium, large)
export WHISPER_MODEL=base

# Porta da aplicação
export PORT=8000
```

### Modelos Disponíveis

| Modelo | Tamanho | Velocidade | Qualidade |
|--------|---------|------------|-----------|
| `tiny` | 39 MB | Muito rápido | Básica |
| `base` | 74 MB | Rápido | Boa |
| `small` | 244 MB | Médio | Muito boa |
| `medium` | 769 MB | Lento | Excelente |
| `large-v3` | 1550 MB | Muito lento | Superior |

## 🐳 Docker

### Build da Imagem

```bash
docker build -t faster-whisper-api .
```

### Executar Container

```bash
docker run -p 8000:8000 faster-whisper-api
```

### Docker Compose

```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Logs
docker-compose logs -f

# Rebuild
docker-compose up --build
```

## 🔧 Desenvolvimento

### Executar em modo desenvolvimento

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testar a API

```bash
# Health check
curl http://localhost:8000/health

# Testar com arquivo de exemplo
curl -X POST "http://localhost:8000/transcribe" \
     -F "file=@test_audio.wav"
```

## 📊 Performance

A API está otimizada para CPU com as seguintes configurações:

- **Quantização INT8**: Reduz uso de memória e melhora velocidade
- **VAD Filter**: Remove silêncios desnecessários
- **Beam Size**: Configurável para balancear velocidade vs qualidade
- **OMP Threads**: Limitado a 4 threads para evitar sobrecarga

### Benchmarks Típicos (CPU)

| Modelo | Arquivo 1min | Memória RAM | Tempo |
|--------|--------------|-------------|-------|
| tiny | MP3 | ~500MB | ~5s |
| base | MP3 | ~800MB | ~15s |
| small | MP3 | ~1.2GB | ~45s |

## 🚨 Limitações

- Arquivos muito grandes (>100MB) podem causar timeout
- Uso intensivo de CPU durante transcrição
- Primeiro carregamento do modelo pode demorar
- Máximo de upload configurado pelo FastAPI

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 🔗 Links Úteis

- [Faster-Whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [FastAPI Documentação](https://fastapi.tiangolo.com/)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Docker Hub](https://hub.docker.com/)

## 📞 Suporte

Se você encontrar problemas ou tiver dúvidas:

1. Verifique a documentação acima
2. Confira os logs: `docker-compose logs -f`
3. Teste o health check: `curl http://localhost:8000/health`
4. Abra uma issue no repositório 