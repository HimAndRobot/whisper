#!/usr/bin/env python3
"""
Script simples para testar a API Faster-Whisper
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_health_check(base_url="http://localhost:8000"):
    """Testa o health check da API"""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check: OK")
            print(f"   Status: {response.json()}")
            return True
        else:
            print(f"❌ Health check falhou: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API")
        print("   Certifique-se de que a API está rodando em http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

def test_root_endpoint(base_url="http://localhost:8000"):
    """Testa o endpoint raiz"""
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Endpoint raiz: OK")
            print(f"   Resposta: {response.json()['message']}")
            return True
        else:
            print(f"❌ Endpoint raiz falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no endpoint raiz: {e}")
        return False

def create_test_audio_file():
    """Cria um arquivo de áudio de teste simples usando texto"""
    try:
        # Criar um arquivo de exemplo com texto
        test_content = """
        Este é um arquivo de teste para a API Faster-Whisper.
        Você pode substituir este arquivo por um arquivo de áudio real
        nos formatos MP3, WAV, M4A, OGG, FLAC ou AAC.
        """
        
        with open("test_audio_info.txt", "w", encoding="utf-8") as f:
            f.write(test_content)
        
        print("📝 Arquivo de teste criado: test_audio_info.txt")
        print("   Para testar com áudio real, adicione um arquivo de áudio na pasta")
        return "test_audio_info.txt"
    
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de teste: {e}")
        return None

def find_audio_files():
    """Procura por arquivos de áudio na pasta atual"""
    audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
    current_dir = Path('.')
    
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(current_dir.glob(f"*{ext}"))
        audio_files.extend(current_dir.glob(f"*{ext.upper()}"))
    
    return audio_files

def test_transcription(base_url="http://localhost:8000", audio_file=None):
    """Testa a transcrição de áudio"""
    if not audio_file:
        # Procurar arquivos de áudio
        audio_files = find_audio_files()
        if audio_files:
            audio_file = audio_files[0]
            print(f"📁 Arquivo de áudio encontrado: {audio_file}")
        else:
            print("⚠️  Nenhum arquivo de áudio encontrado para teste")
            print("   Adicione um arquivo de áudio (MP3, WAV, etc.) na pasta para testar")
            return False
    
    try:
        print(f"🎵 Testando transcrição com: {audio_file}")
        
        with open(audio_file, 'rb') as f:
            files = {'file': f}
            data = {
                'beam_size': 5,
                'language': 'pt',  # Português
                'word_timestamps': False,
                'vad_filter': True
            }
            
            print("   Enviando arquivo para transcrição...")
            start_time = time.time()
            
            response = requests.post(
                f"{base_url}/transcribe",
                files=files,
                data=data,
                timeout=120  # 2 minutos de timeout
            )
            
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Transcrição concluída com sucesso!")
                print(f"   Tempo: {end_time - start_time:.2f}s")
                print(f"   Idioma detectado: {result.get('language', 'N/A')}")
                print(f"   Probabilidade: {result.get('language_probability', 0):.2f}")
                print(f"   Texto: {result.get('text', 'N/A')[:100]}...")
                print(f"   Segmentos: {len(result.get('segments', []))}")
                return True
            else:
                print(f"❌ Transcrição falhou: {response.status_code}")
                print(f"   Erro: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Timeout na transcrição (>2 minutos)")
        return False
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {audio_file}")
        return False
    except Exception as e:
        print(f"❌ Erro na transcrição: {e}")
        return False

def main():
    """Função principal para executar todos os testes"""
    print("🚀 Testando API Faster-Whisper")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Teste 1: Health Check
    print("\n1. Testando Health Check...")
    health_ok = test_health_check(base_url)
    
    if not health_ok:
        print("\n❌ API não está funcionando. Verifique se ela está rodando:")
        print("   - Localmente: python main.py")
        print("   - Docker: docker-compose up")
        sys.exit(1)
    
    # Teste 2: Endpoint raiz
    print("\n2. Testando endpoint raiz...")
    root_ok = test_root_endpoint(base_url)
    
    # Teste 3: Transcrição (opcional)
    print("\n3. Testando transcrição...")
    audio_files = find_audio_files()
    
    if audio_files:
        transcription_ok = test_transcription(base_url, audio_files[0])
    else:
        print("⚠️  Pulando teste de transcrição (nenhum arquivo de áudio encontrado)")
        print("   Para testar transcrição, adicione um arquivo de áudio na pasta")
        transcription_ok = True  # Não falhar se não tiver áudio
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    print(f"   Health Check: {'✅ OK' if health_ok else '❌ FALHOU'}")
    print(f"   Endpoint Raiz: {'✅ OK' if root_ok else '❌ FALHOU'}")
    
    if audio_files:
        print(f"   Transcrição: {'✅ OK' if transcription_ok else '❌ FALHOU'}")
    else:
        print("   Transcrição: ⚠️  PULADO (sem arquivo de áudio)")
    
    print(f"\n🌐 Acesse a documentação em: {base_url}/docs")
    
    if health_ok and root_ok:
        print("🎉 API está funcionando corretamente!")
    else:
        print("❌ Alguns testes falharam. Verifique os logs acima.")

if __name__ == "__main__":
    main() 