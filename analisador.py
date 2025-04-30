import argparse
import os
import time
import psutil
import lizard
import csv
import matplotlib.pyplot as plt


def measure_script(file_path):
    ext = os.path.splitext(file_path)[1]
    if ext == '.py':
        cmd = ['python3', file_path]
    elif ext == '.js':
        cmd = ['node', file_path]
    elif ext == '.sh':
        cmd = ['bash', file_path]
    else:
        print(f"[!] Extensão não suportada: {file_path}")
        return None, None

    proc = psutil.Popen(cmd)
    start = time.time()

    peak_memory = 0
    try:
        while True:
            if proc.poll() is not None:
                break
            try:
                mem = proc.memory_info().rss
                peak_memory = max(peak_memory, mem)
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                break
            time.sleep(0.05) 
    finally:
        proc.wait()

    elapsed = time.time() - start
    return elapsed, peak_memory

def analyze_static_with_lizard(file_path):
    """Usa lizard para obter complexidade, funções, e LOC."""
    result = lizard.analyze_file(file_path)
    total_complexity = sum(f.cyclomatic_complexity for f in result.function_list)
    most_complex = max([f.cyclomatic_complexity for f in result.function_list], default=0)
    function_count = len(result.function_list)
    effective_loc = result.nloc  # linhas efetivas
    return {
        'complexity': total_complexity,
        'most_complex_func': most_complex,
        'function_count': function_count,
        'loc_effective': effective_loc
    }


def analyze_file(file_path, runnable_exts):
    """Coleta métricas estáticas com lizard e runtime (se aplicável)."""
    size = os.path.getsize(file_path)
    with open(file_path, 'r', errors='ignore') as f:
        lines = sum(1 for _ in f)

    runtime, memory = None, None
    if os.path.splitext(file_path)[1] in runnable_exts:
        runtime, memory = measure_script(file_path)

    static = analyze_static_with_lizard(file_path)

    return {
        'path': file_path,
        'lines': lines,
        'size': size,
        'runtime': runtime,
        'memory': memory,
        'complexity': static['complexity'],
        'most_complex_func': static['most_complex_func'],
        'function_count': static['function_count'],
        'loc_effective': static['loc_effective']
    }

def gerar_graficos(resultados):
    arquivos = [os.path.basename(r['path']) for r in resultados]

    tempos = [r['runtime'] or 0 for r in resultados]
    memorias = [r['memory'] or 0 for r in resultados]
    complexidades = [r['complexity'] for r in resultados]
    funcoes = [r['function_count'] for r in resultados]

    fig, axs = plt.subplots(2, 2, figsize=(14, 8))
    fig.suptitle("Análise Comparativa de Códigos", fontsize=16)

    axs[0, 0].bar(arquivos, tempos, color='steelblue')
    axs[0, 0].set_title("Tempo de Execução (s)")
    axs[0, 0].set_ylabel("Segundos")
    axs[0, 0].tick_params(axis='x', rotation=45)

    axs[0, 1].bar(arquivos, memorias, color='indianred')
    axs[0, 1].set_title("Pico de Memória (bytes)")
    axs[0, 1].set_ylabel("Bytes")
    axs[0, 1].tick_params(axis='x', rotation=45)

    axs[1, 0].bar(arquivos, complexidades, color='seagreen')
    axs[1, 0].set_title("Complexidade Ciclomática Total")
    axs[1, 0].set_ylabel("Complexidade")
    axs[1, 0].tick_params(axis='x', rotation=45)

    axs[1, 1].bar(arquivos, funcoes, color='orange')
    axs[1, 1].set_title("Número de Funções")
    axs[1, 1].set_ylabel("Funções")
    axs[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.subplots_adjust(top=0.88)

    plt.savefig("analise_resultados.png", bbox_inches='tight')
    print("[✓] Gráfico salvo como analise_resultados.png")



def main():
    parser = argparse.ArgumentParser(
        description='Analisa custo de código (estático + runtime).'
    )
    parser.add_argument(
        '--path', '-p',
        required=True,
        help='Diretório raiz a ser analisado'
    )
    parser.add_argument(
    '--csv',
    help='Caminho para salvar os resultados em CSV (ex: resultados.csv)'
    )
    parser.add_argument(
    '--plot',
    action='store_true',
    help='Exibe gráficos comparativos ao final'
    )
    args = parser.parse_args()

    results = []
    for root, _, files in os.walk(args.path):
        for fname in files:
            if os.path.splitext(fname)[1] in [".py", ".js", ".sh"]:
                fp = os.path.join(root, fname)
                results.append(analyze_file(fp, [".py", ".js", ".sh"]))

    header = f"{'Arquivo':<40}{'LOC':>6}{'EF_LOC':>8}{'Funções':>9}{'Cx Total':>10}{'Cx Máx':>8}{'Tam(B)':>10}{'Tempo(s)':>10}{'Mem(B)':>12}"
    print(header)
    print('-' * len(header))
    for r in results:
        t = f"{r['runtime']:.2f}" if r['runtime'] is not None else '-'
        m = f"{r['memory']}" if r['memory'] is not None else '-'
        print(f"{r['path']:<40}{r['lines']:>6}{r['loc_effective']:>8}{r['function_count']:>9}{r['complexity']:>10}{r['most_complex_func']:>8}{r['size']:>10}{t:>10}{m:>12}")
    
    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Arquivo', 'LOC', 'EF_LOC', 'Funções', 'Cx Total', 'Cx Máx', 'Tam(B)', 'Tempo(s)', 'Mem(B)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow({
                    'Arquivo': r['path'],
                    'LOC': r['lines'],
                    'EF_LOC': r['loc_effective'],
                    'Funções': r['function_count'],
                    'Cx Total': r['complexity'],
                    'Cx Máx': r['most_complex_func'],
                    'Tam(B)': r['size'],
                    'Tempo(s)': f"{r['runtime']:.2f}" if r['runtime'] is not None else '',
                    'Mem(B)': r['memory'] if r['memory'] is not None else ''
                })
        print(f"\n[✓] Resultados exportados para {args.csv}")
    if args.plot:
        gerar_graficos(results)


if __name__ == '__main__':
    main()
