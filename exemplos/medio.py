# codigo_medio.py
import time

def processo_medio():
    total = 0
    for i in range(1_000_000):
        total += i
    time.sleep(1)  # adiciona 1 segundo forçado
    return total

if __name__ == "__main__":
    processo_medio()
