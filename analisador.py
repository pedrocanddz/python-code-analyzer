#!/usr/bin/env python3
import argparse
import os
import time
import psutil
import lizard
import csv
import matplotlib.pyplot as plt

def measure_script(file_path):
    ext = os.path.splitext(file_path)[1]
    cmds = {
        '.py': ['python3', file_path],
        '.js': ['node', file_path],
        '.sh': ['bash', file_path],
    }
    cmd = cmds.get(ext)
    if not cmd:
        print(f"[!] Extensão não suportada: {file_path}")
        return None, None, None, None

    proc = psutil.Popen(cmd)
    start = time.time()
    peak_memory = 0

    proc.cpu_percent(interval=None)
    cpu_samples = []

    while proc.poll() is None:
        try:
            mem = proc.memory_info().rss
            peak_memory = max(peak_memory, mem)
            cpu = proc.cpu_percent(interval=None)
            cpu_samples.append(cpu)
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            break
        time.sleep(0.05) #Pra pegar as métricas melhor

    proc.wait()
    elapsed = time.time() - start

    # média de uso de CPU
    avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0

    # estimativa de potência e energia
    num_cores = psutil.cpu_count(logical=True)
    nominal_power_per_core = 10
    power = (avg_cpu / 100) * num_cores * nominal_power_per_core
    energy_joules = power * elapsed

    return elapsed, peak_memory, power, energy_joules

def analyze_static_with_lizard(file_path):
    result = lizard.analyze_file(file_path)
    total_complexity = sum(f.cyclomatic_complexity for f in result.function_list)
    most_complex = max((f.cyclomatic_complexity for f in result.function_list), default=0)
    function_count = len(result.function_list)
    effective_loc = result.nloc
    return {
        'complexity': total_complexity,
        'most_complex_func': most_complex,
        'function_count': function_count,
        'loc_effective': effective_loc
    }

def analyze_file(file_path, runnable_exts):
    size = os.path.getsize(file_path)
    with open(file_path, 'r', errors='ignore') as f:
        lines = sum(1 for _ in f)

    runtime, memory, power, energy = None, None, None, None
    if os.path.splitext(file_path)[1] in runnable_exts:
        runtime, memory, power, energy = measure_script(file_path)

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
        'loc_effective': static['loc_effective'],
        'power': power,
        'energy': energy
    }

def gerar_graficos(resultados):
    arquivos = [os.path.basename(r['path']) for r in resultados]

    tempos = [r['runtime'] or 0 for r in resultados]
    memorias = [r['memory'] or 0 for r in resultados]
    complexidades = [r['complexity'] for r in resultados]
    funcoes = [r['function_count'] for r in resultados]
    watts = [r['power'] or 0 for r in resultados]
    joules = [r['energy'] or 0 for r in resultados]

    fig, axs = plt.subplots(3, 2, figsize=(14, 12))
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
    axs[1, 0].set_title("Complexidade Ciclomática")
    axs[1, 0].set_ylabel("Complexidade")
    axs[1, 0].tick_params(axis='x', rotation=45)

    axs[1, 1].bar(arquivos, funcoes, color='orange')
    axs[1, 1].set_title("Número de Funções")
    axs[1, 1].set_ylabel("Funções")
    axs[1, 1].tick_params(axis='x', rotation=45)

    axs[2, 0].bar(arquivos, watts, color='mediumpurple')
    axs[2, 0].set_title("Potência Estimada (W)")
    axs[2, 0].set_ylabel("Watts")
    axs[2, 0].tick_params(axis='x', rotation=45)

    axs[2, 1].bar(arquivos, joules, color='darkcyan')
    axs[2, 1].set_title("Energia Estimada (J)")
    axs[2, 1].set_ylabel("Joules")
    axs[2, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.savefig("analise_resultados.png", bbox_inches='tight')
    print("[✓] Gráfico salvo como analise_resultados.png")

def main():
    parser = argparse.ArgumentParser(description='Analisa custo de código (estático + runtime).')
    parser.add_argument('--path', '-p', required=True, help='Diretório raiz a ser analisado')
    parser.add_argument('--csv', help='Caminho para salvar os resultados em CSV (ex: resultados.csv)')
    parser.add_argument('--plot', action='store_true', help='Exibe gráficos comparativos ao final')
    args = parser.parse_args()

    results = []
    for root, _, files in os.walk(args.path):
        for fname in files:
            if os.path.splitext(fname)[1] in ['.py', '.js', '.sh']:
                fp = os.path.join(root, fname)
                results.append(analyze_file(fp, ['.py', '.js', '.sh']))

    header = (
        f"{'Arquivo':<40}{'LOC':>6}{'EF_LOC':>8}{'Funções':>9}"
        f"{'Cx Total':>10}{'Cx Máx':>8}{'Tam(B)':>10}"
        f"{'Tempo(s)':>10}{'Mem(B)':>12}{'Watt':>8}{'Joules':>10}"
    )
    print(header)
    print('-' * len(header))
    for r in results:
        t = f"{r['runtime']:.2f}" if r['runtime'] is not None else '0.00'
        m = f"{r['memory']}" if r['memory'] is not None else '0'
        p = f"{r['power']:.2f}"
        e = f"{r['energy']:.2f}"
        print(
            f"{r['path']:<40}{r['lines']:>6}{r['loc_effective']:>8}"
            f"{r['function_count']:>9}{r['complexity']:>10}{r['most_complex_func']:>8}"
            f"{r['size']:>10}{t:>10}{m:>12}{p:>8}{e:>10}"
        )

    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Arquivo','LOC','EF_LOC','Funções','Cx Total','Cx Máx',
                          'Tam(B)','Tempo(s)','Mem(B)','Watt','Joules']
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
                    'Tempo(s)': f"{r['runtime']:.2f}",
                    'Mem(B)': r['memory'],
                    'Watt': f"{r['power']:.2f}",
                    'Joules': f"{r['energy']:.2f}"
                })
        print(f"\n[✓] Resultados exportados para {args.csv}")

    if args.plot:
        gerar_graficos(results)

if __name__ == '__main__':
    main()