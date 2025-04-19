# codigo_longo.py
import time

def processo_pesado():
    matriz = [[i * j for j in range(500)] for i in range(500)]
    soma = sum(sum(linha) for linha in matriz)
    time.sleep(2)  # adiciona 2 segundos forçado
    return soma

if __name__ == "__main__":
    processo_pesado()
