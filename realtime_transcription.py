"""
Transcrição em tempo real usando microfone
"""

import pyaudio
import wave
import threading
import queue
import time
import os
import logging
from faster_whisper import WhisperModel
from config import config

# Configurar logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class RealTimeTranscriber:
    """
    Classe para transcrição em tempo real do microfone
    """
    
    def __init__(self):
        """
        Inicializa o transcritor em tempo real
        """
        # Configurações de áudio
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.RECORD_SECONDS = 3  # Gravar em chunks de 3 segundos
        
        # Inicializar PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Fila para armazenar chunks de áudio
        self.audio_queue = queue.Queue()
        
        # Controle de execução
        self.is_recording = False
        self.is_transcribing = False
        
        # Carregar modelo Whisper
        logger.info(f"Carregando modelo Whisper: {config.WHISPER_MODEL}")
        self.model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE
        )
        logger.info("Modelo carregado com sucesso!")
        
        # Configurar threads
        os.environ["OMP_NUM_THREADS"] = str(config.OMP_NUM_THREADS)
    
    def start_recording(self):
        """
        Inicia a gravação do microfone
        """
        try:
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.is_recording = True
            logger.info("Gravação iniciada. Fale no microfone...")
            
            # Thread para capturar áudio
            self.record_thread = threading.Thread(target=self._record_audio)
            self.record_thread.daemon = True
            self.record_thread.start()
            
            # Thread para transcrição
            self.transcribe_thread = threading.Thread(target=self._transcribe_audio)
            self.transcribe_thread.daemon = True
            self.transcribe_thread.start()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar gravação: {e}")
            raise
    
    def stop_recording(self):
        """
        Para a gravação e transcrição
        """
        self.is_recording = False
        self.is_transcribing = False
        
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        
        self.audio.terminate()
        logger.info("Gravação interrompida.")
    
    def _record_audio(self):
        """
        Captura áudio do microfone em chunks
        """
        frames = []
        chunk_count = 0
        frames_per_chunk = int(self.RATE / self.CHUNK * self.RECORD_SECONDS)
        
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK)
                frames.append(data)
                chunk_count += 1
                
                # Quando completar um chunk, adicionar à fila
                if chunk_count >= frames_per_chunk:
                    self.audio_queue.put(frames.copy())
                    frames.clear()
                    chunk_count = 0
                    
            except Exception as e:
                logger.error(f"Erro na captura de áudio: {e}")
                break
    
    def _transcribe_audio(self):
        """
        Transcreve chunks de áudio da fila
        """
        self.is_transcribing = True
        
        while self.is_transcribing or not self.audio_queue.empty():
            try:
                # Pegar chunk da fila (timeout para não bloquear)
                frames = self.audio_queue.get(timeout=1)
                
                # Salvar chunk como arquivo temporário
                temp_filename = f"temp_chunk_{int(time.time())}.wav"
                
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                    wf.setframerate(self.RATE)
                    wf.writeframes(b''.join(frames))
                
                # Transcrever chunk
                segments, info = self.model.transcribe(
                    temp_filename,
                    beam_size=config.DEFAULT_BEAM_SIZE,
                    vad_filter=config.DEFAULT_VAD_FILTER,
                    word_timestamps=config.DEFAULT_WORD_TIMESTAMPS,
                    language=config.DEFAULT_LANGUAGE  # Usar idioma configurado
                )
                
                # Processar resultado
                text = ""
                for segment in segments:
                    text += segment.text
                
                # Mostrar resultado se não estiver vazio
                if text.strip():
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {text.strip()}")
                
                # Limpar arquivo temporário
                os.remove(temp_filename)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erro na transcrição: {e}")
                if 'temp_filename' in locals() and os.path.exists(temp_filename):
                    os.remove(temp_filename)
    
    def run(self):
        """
        Executa o transcritor em tempo real
        """
        try:
            print("=== Transcritor em Tempo Real ===")
            print(f"Modelo: {config.WHISPER_MODEL}")
            print(f"Device: {config.WHISPER_DEVICE}")
            print(f"Compute Type: {config.WHISPER_COMPUTE_TYPE}")
            print(f"Idioma: {config.DEFAULT_LANGUAGE}")
            print("Pressione Ctrl+C para parar\n")
            
            self.start_recording()
            
            # Manter execução
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nParando transcrição...")
            self.stop_recording()
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            self.stop_recording()

def main():
    """
    Função principal para executar o transcritor
    """
    # Validar configuração
    validation = config.validate_config()
    if not validation["valid"]:
        logger.error("Configuração inválida:")
        for issue in validation["issues"]:
            logger.error(f"  - {issue}")
        return
    
    # Criar e executar transcritor
    transcriber = RealTimeTranscriber()
    transcriber.run()

if __name__ == "__main__":
    main() 