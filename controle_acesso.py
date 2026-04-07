import time
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Configuração dos Pinos dos LEDs (Padrão BCM)
PINO_LED_VERDE = 2
PINO_LED_VERMELHO = 3

# Configuração da GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PINO_LED_VERDE, GPIO.OUT)
GPIO.setup(PINO_LED_VERMELHO, GPIO.OUT)

# Instanciamento da biblioteca (conforme a imagem)
leitorRfid = SimpleMFRC522()

# Banco de dados simulado de colaboradores
# Formato: { id_da_tag: {"nome": "Nome da Pessoa", "acesso": True/False} }
banco_de_dados = {
    484055668844: {"nome": "Leonardo Cambrussi", "acesso": True},
    358265126532: {"nome": "Greice Dalmoro", "acesso": False}
}

# Variáveis de controle de estado e relatórios
colaboradores_na_sala = set()
ja_entraram_hoje = set()
hora_entrada = {}
tempo_total_permanencia = {}
tentativas_nao_autorizadas = {}
tentativas_invasao = 0

def acionar_led_verde():
    """Acende o LED verde por 5 segundos."""
    GPIO.output(PINO_LED_VERDE, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(PINO_LED_VERDE, GPIO.LOW)

def acionar_led_vermelho():
    """Acende o LED vermelho por 5 segundos."""
    GPIO.output(PINO_LED_VERMELHO, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(PINO_LED_VERMELHO, GPIO.LOW)

def piscar_led_vermelho():
    """Pisca o LED vermelho 10 vezes (indicação de invasão)."""
    for _ in range(10):
        GPIO.output(PINO_LED_VERMELHO, GPIO.HIGH)
        time.sleep(0.25)
        GPIO.output(PINO_LED_VERMELHO, GPIO.LOW)
        time.sleep(0.25)

def gerar_relatorio():
    """Gera o relatório final ao encerrar o programa."""
    print("\n\n" + "="*40)
    print(" RELATÓRIO DE ACESSO DO PROJETO ".center(40, "="))
    print("="*40)
    
    agora = time.time()
    for tag_id in list(colaboradores_na_sala):
        tempo_sessao = agora - hora_entrada[tag_id]
        tempo_total_permanencia[tag_id] = tempo_total_permanencia.get(tag_id, 0) + tempo_sessao
    
    print("\n[ TEMPO DE PERMANÊNCIA (AUTORIZADOS) ]")
    if not tempo_total_permanencia:
        print("Nenhum colaborador autorizado acessou a sala hoje.")
    else:
        for tag_id, segundos in tempo_total_permanencia.items():
            nome = banco_de_dados[tag_id]["nome"]
            horas = int(segundos // 3600)
            minutos = int((segundos % 3600) // 60)
            segundos_restantes = int(segundos % 60)
            print(f"- {nome}: {horas}h {minutos}m {segundos_restantes}s")

    print("\n[ TENTATIVAS DE ACESSO NÃO AUTORIZADAS ]")
    if not tentativas_nao_autorizadas:
        print("Nenhuma tentativa de acesso negado registrada.")
    else:
        for tag_id, qtd in tentativas_nao_autorizadas.items():
            nome = banco_de_dados[tag_id]["nome"]
            print(f"- {nome}: {qtd} tentativa(s)")

    print("\n[ TENTATIVAS DE INVASÃO (TAGS DESCONHECIDAS) ]")
    print(f"- Total de tentativas: {tentativas_invasao}")
    print("="*40 + "\n")

try:
    print("Sistema de Controle de Acesso Iniciado.")
    print("Aguardando leitura da tag (Sem bloqueio da thread)...")
    print("Pressione Ctrl+C para encerrar e gerar o relatório.")
    
    while True:
        # Utilizando o método não bloqueante conforme a imagem
        tag = leitorRfid.read_id_no_block()
        
        if tag is not None:
            agora = time.time()
            print(f"\nID do cartao lido: {tag}")
            
            # 1. Verifica se a tag existe no banco de dados
            if tag in banco_de_dados:
                colaborador = banco_de_dados[tag]
                nome = colaborador["nome"]
                
                # 2. Verifica se tem autorização para o projeto
                if colaborador["acesso"]:
                    
                    # 3. Lógica de Entrada e Saída
                    if tag in colaboradores_na_sala:
                        # Registrando SAÍDA
                        tempo_sessao = agora - hora_entrada[tag]
                        tempo_total_permanencia[tag] = tempo_total_permanencia.get(tag, 0) + tempo_sessao
                        colaboradores_na_sala.remove(tag)
                        
                        print(f"Saída registrada. Até logo, {nome}!")
                        acionar_led_verde()
                        
                    else:
                        # Registrando ENTRADA
                        hora_entrada[tag] = agora
                        colaboradores_na_sala.add(tag)
                        
                        if tag not in ja_entraram_hoje:
                            print(f"Bem-vindo, {nome}")
                            ja_entraram_hoje.add(tag)
                        else:
                            print(f"Bem-vindo de volta, {nome}")
                        
                        acionar_led_verde()
                        
                else:
                    # Colaborador sem acesso
                    print(f"Você não tem acesso a este projeto, {nome}")
                    tentativas_nao_autorizadas[tag] = tentativas_nao_autorizadas.get(tag, 0) + 1
                    acionar_led_vermelho()
                    
            else:
                # Tag desconhecida (Possível Invasão)
                print("Identificação não encontrada!")
                tentativas_invasao += 1
                piscar_led_vermelho()

            # Atraso extra após processar uma leitura para evitar duplicidades
            time.sleep(1)
            
        else:
            # Como não é bloqueante, usamos um pequeno sleep para não sobrecarregar a CPU
            time.sleep(0.1)

except KeyboardInterrupt:
    gerar_relatorio()

finally:
    GPIO.cleanup()
    print("Programa encerrado.")