# Passo 1: Importar a biblioteca correta
import mariadb 
import sys
import traceback
import datetime
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

def conectar_db():
    # Passo 2: Usar o objeto 'mariadb' para conectar
    return mariadb.connect(
        host='localhost',
        user='root',
        password='123',  # Sua senha
        database='controle_refeitorio'
    )

# O restante do arquivo continua igual...
def buscar_aluno_por_id(id_str):
    try:
        id_int = int(id_str)
        print(f'Consultando aluno com ID: {id_int}')
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alunos WHERE id = ?', (id_int,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        aluno = dict(zip(columns, row)) if row else None
        if aluno:
            print('Aluno encontrado:', aluno)
        else:
            print('Aluno não encontrado')
        cursor.close()
        conn.close()
        return aluno
    except Exception as e:
        print(f'Erro ao consultar aluno: {e}')
        return None

def excecao_nao_tratada(exctype, value, tb):
    print("Exceção não tratada na aplicação:", exctype, value)
    traceback.print_tb(tb)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = excecao_nao_tratada

import mariadb
import sys
import traceback
import datetime
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

def conectar_db():
    return mariadb.connect(
        host='localhost',
        user='root',
        password='123',  # Altere para sua senha, se necessário
        database='controle_refeitorio'
    )

def aluno_com_entrada_aberta(aluno_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM registros_refeitorio WHERE aluno_id = ? AND hora_saida IS NULL', (aluno_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    registro = dict(zip(columns, row)) if row else None
    cursor.close()
    conn.close()
    return registro

def salvar_foto_em_bytes(foto_np):
    # Converte imagem numpy (BGR) para JPEG em bytes
    img_rgb = cv2.cvtColor(foto_np, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    buf = BytesIO()
    pil_img.save(buf, format='JPEG')
    return buf.getvalue()

def registrar_entrada_ou_saida(aluno_id, foto_np):
    agora = datetime.datetime.now()
    foto_bytes = salvar_foto_em_bytes(foto_np) if foto_np is not None else None
    registro_aberto = aluno_com_entrada_aberta(aluno_id)
    conn = conectar_db()
    cursor = conn.cursor()
    if registro_aberto:
        # Já tem entrada aberta, registrar saída (sem foto se não enviada)
        if foto_bytes is not None:
            cursor.execute('UPDATE registros_refeitorio SET hora_saida = ?, foto = ? WHERE id = ?',
                           (agora, foto_bytes, registro_aberto['id']))
        else:
            cursor.execute('UPDATE registros_refeitorio SET hora_saida = ? WHERE id = ?',
                           (agora, registro_aberto['id']))
        conn.commit()
        cursor.close()
        conn.close()
        return 'saida', agora
    else:
        # Não tem entrada aberta, registrar entrada (com foto)
        cursor.execute('INSERT INTO registros_refeitorio (aluno_id, foto, hora_entrada) VALUES (?, ?, ?)',
                       (aluno_id, foto_bytes, agora))
        conn.commit()
        cursor.close()
        conn.close()
        return 'entrada', agora

def relatorio_entradas_por_turno(data_inicio=None, data_fim=None):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        if data_inicio is None:
            data_inicio = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if data_fim is None:
            data_fim = datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Definindo os 4 turnos específicos
        cafe_manha_inicio = datetime.time(9, 30)
        cafe_manha_fim = datetime.time(9, 50)
        almoco_inicio = datetime.time(11, 0)
        almoco_fim = datetime.time(12, 50)
        cafe_tarde_inicio = datetime.time(14, 30)
        cafe_tarde_fim = datetime.time(14, 50)
        janta_inicio = datetime.time(19, 30)
        janta_fim = datetime.time(20, 40)
        
        query = """
        SELECT 
            CASE 
                WHEN TIME(hora_entrada) BETWEEN ? AND ? THEN 'Café da Manhã'
                WHEN TIME(hora_entrada) BETWEEN ? AND ? THEN 'Almoço'
                WHEN TIME(hora_entrada) BETWEEN ? AND ? THEN 'Café da Tarde'
                WHEN TIME(hora_entrada) BETWEEN ? AND ? THEN 'Janta'
                ELSE 'Outros'
            END as turno,
            COUNT(*) as total_entradas,
            COUNT(DISTINCT aluno_id) as alunos_unicos
        FROM registros_refeitorio 
        WHERE hora_entrada BETWEEN ? AND ?
        GROUP BY turno
        ORDER BY 
            CASE turno
                WHEN 'Café da Manhã' THEN 1
                WHEN 'Almoço' THEN 2
                WHEN 'Café da Tarde' THEN 3
                WHEN 'Janta' THEN 4
                ELSE 5
            END
        """
        
        cursor.execute(query, (
            cafe_manha_inicio, cafe_manha_fim,
            almoco_inicio, almoco_fim,
            cafe_tarde_inicio, cafe_tarde_fim,
            janta_inicio, janta_fim,
            data_inicio, data_fim
        ))
        
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return resultados
        
    except Exception as e:
        print(f'Erro ao gerar relatório por turno: {e}')
        return []

def relatorio_semanal(data_inicio=None, turnos_filtro=None):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        if data_inicio is None:
            hoje = datetime.datetime.now()
            dias_para_segunda = hoje.weekday()
            data_inicio = hoje - datetime.timedelta(days=dias_para_segunda)
            data_inicio = data_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        
        data_fim = data_inicio + datetime.timedelta(days=7)
        
        # Definindo os 4 turnos específicos
        cafe_manha_inicio = datetime.time(9, 30)
        cafe_manha_fim = datetime.time(9, 50)
        almoco_inicio = datetime.time(11, 0)
        almoco_fim = datetime.time(12, 50)
        cafe_tarde_inicio = datetime.time(14, 30)
        cafe_tarde_fim = datetime.time(14, 50)
        janta_inicio = datetime.time(19, 30)
        janta_fim = datetime.time(20, 40)
        
        # Construir filtro de turnos se especificado
        turno_conditions = []
        turno_params = []
        
        if turnos_filtro:
            for turno in turnos_filtro:
                if turno == 'Café da Manhã':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_manha_inicio, cafe_manha_fim])
                elif turno == 'Almoço':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([almoco_inicio, almoco_fim])
                elif turno == 'Café da Tarde':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_tarde_inicio, cafe_tarde_fim])
                elif turno == 'Janta':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([janta_inicio, janta_fim])
        
        # Construir query base
        query = """
        SELECT 
            DATE(hora_entrada) as data,
            COUNT(*) as total_entradas,
            COUNT(DISTINCT aluno_id) as alunos_unicos
        FROM registros_refeitorio 
        WHERE hora_entrada BETWEEN ? AND ?
        """
        
        params = [data_inicio, data_fim]
        
        # Adicionar filtro de turnos se especificado
        if turno_conditions:
            query += " AND (" + " OR ".join(turno_conditions) + ")"
            params.extend(turno_params)
        
        query += """
        GROUP BY DATE(hora_entrada)
        ORDER BY data
        """
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return resultados
        
    except Exception as e:
        print(f'Erro ao gerar relatório semanal: {e}')
        return []

def relatorio_mensal(ano=None, mes=None, turnos_filtro=None):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        if ano is None or mes is None:
            hoje = datetime.datetime.now()
            ano = hoje.year
            mes = hoje.month
        
        data_inicio = datetime.datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime.datetime(ano + 1, 1, 1)
        else:
            data_fim = datetime.datetime(ano, mes + 1, 1)
        
        # Definindo os 4 turnos específicos
        cafe_manha_inicio = datetime.time(9, 30)
        cafe_manha_fim = datetime.time(9, 50)
        almoco_inicio = datetime.time(11, 0)
        almoco_fim = datetime.time(12, 50)
        cafe_tarde_inicio = datetime.time(14, 30)
        cafe_tarde_fim = datetime.time(14, 50)
        janta_inicio = datetime.time(19, 30)
        janta_fim = datetime.time(20, 40)
        
        # Construir filtro de turnos se especificado
        turno_conditions = []
        turno_params = []
        
        if turnos_filtro:
            for turno in turnos_filtro:
                if turno == 'Café da Manhã':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_manha_inicio, cafe_manha_fim])
                elif turno == 'Almoço':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([almoco_inicio, almoco_fim])
                elif turno == 'Café da Tarde':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_tarde_inicio, cafe_tarde_fim])
                elif turno == 'Janta':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([janta_inicio, janta_fim])
        
        # Construir query base
        query = """
        SELECT 
            DATE(hora_entrada) as data,
            COUNT(*) as total_entradas,
            COUNT(DISTINCT aluno_id) as alunos_unicos
        FROM registros_refeitorio 
        WHERE hora_entrada BETWEEN ? AND ?
        """
        
        params = [data_inicio, data_fim]
        
        # Adicionar filtro de turnos se especificado
        if turno_conditions:
            query += " AND (" + " OR ".join(turno_conditions) + ")"
            params.extend(turno_params)
        
        query += """
        GROUP BY DATE(hora_entrada)
        ORDER BY data
        """
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return resultados
        
    except Exception as e:
        print(f'Erro ao gerar relatório mensal: {e}')
        return []

def dados_grafico_frequencia_tempo(data_inicio=None, data_fim=None, intervalo_horas=1):
    """
    Gera dados para gráfico de frequência por intervalo de tempo
    """
    try:
        print(f"=== DEBUG: dados_grafico_frequencia_tempo chamado ===")
        print(f"DEBUG: data_inicio = {data_inicio}")
        print(f"DEBUG: data_fim = {data_fim}")
        
        conn = conectar_db()
        cursor = conn.cursor()
        
        if data_inicio is None:
            data_inicio = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if data_fim is None:
            data_fim = datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"DEBUG: Após ajustes - data_inicio = {data_inicio}")
        print(f"DEBUG: Após ajustes - data_fim = {data_fim}")
        
        query = """
        SELECT 
            DATE_FORMAT(hora_entrada, '%Y-%m-%d %H:00:00') as intervalo,
            COUNT(*) as total_entradas
        FROM registros_refeitorio 
        WHERE hora_entrada BETWEEN ? AND ?
        GROUP BY DATE_FORMAT(hora_entrada, '%Y-%m-%d %H:00:00')
        ORDER BY intervalo
        """
        
        print(f"DEBUG: Query SQL: {query}")
        print(f"DEBUG: Parâmetros: data_inicio={data_inicio}, data_fim={data_fim}")
        
        cursor.execute(query, (data_inicio, data_fim))
        resultados = cursor.fetchall()
        
        print(f"DEBUG: Resultados obtidos: {resultados}")
        print(f"DEBUG: Quantidade de resultados: {len(resultados)}")
        
        cursor.close()
        conn.close()
        
        return resultados
        
    except Exception as e:
        print(f'Erro ao gerar dados para gráfico: {e}')
        import traceback
        traceback.print_exc()
        return []

def gerar_grafico_frequencia(data_inicio=None, data_fim=None, salvar_arquivo='grafico_frequencia.png'):
    """
    Gera e salva um gráfico de frequência por hora
    """
    try:
        dados = dados_grafico_frequencia_tempo(data_inicio, data_fim)
        
        if not dados:
            print("Nenhum dado encontrado para o período especificado")
            return False
        
        # Preparar dados para o gráfico
        datas = []
        entradas = []
        
        for intervalo, total in dados:
            datas.append(datetime.datetime.strptime(intervalo, '%Y-%m-%d %H:%M:%S'))
            entradas.append(total)
        
        # Criar gráfico
        plt.figure(figsize=(12, 6))
        plt.plot(datas, entradas, marker='o', linewidth=2, markersize=6)
        plt.title('Frequência de Entradas por Hora', fontsize=16, fontweight='bold')
        plt.xlabel('Hora', fontsize=12)
        plt.ylabel('Número de Entradas', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Formatar eixo X
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(salvar_arquivo, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Gráfico salvo como: {salvar_arquivo}")
        return True
        
    except Exception as e:
        print(f'Erro ao gerar gráfico: {e}')
        return False

def relatorio_diario(data=None, turnos_filtro=None):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        if data is None:
            data = datetime.datetime.now().date()
        
        # Definindo os 4 turnos específicos
        cafe_manha_inicio = datetime.time(9, 30)
        cafe_manha_fim = datetime.time(9, 50)
        almoco_inicio = datetime.time(11, 0)
        almoco_fim = datetime.time(12, 50)
        cafe_tarde_inicio = datetime.time(14, 30)
        cafe_tarde_fim = datetime.time(14, 50)
        janta_inicio = datetime.time(19, 30)
        janta_fim = datetime.time(20, 40)
        
        # Construir filtro de turnos se especificado
        turno_conditions = []
        turno_params = []
        
        if turnos_filtro:
            for turno in turnos_filtro:
                if turno == 'Café da Manhã':
                    turno_conditions.append("(TIME(r.hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_manha_inicio, cafe_manha_fim])
                elif turno == 'Almoço':
                    turno_conditions.append("(TIME(r.hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([almoco_inicio, almoco_fim])
                elif turno == 'Café da Tarde':
                    turno_conditions.append("(TIME(r.hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_tarde_inicio, cafe_tarde_fim])
                elif turno == 'Janta':
                    turno_conditions.append("(TIME(r.hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([janta_inicio, janta_fim])
        
        # Construir query base
        query = """
        SELECT 
            r.hora_entrada,
            r.hora_saida,
            a.nome,
            a.matricula,
            a.curso,
            CASE 
                WHEN TIME(r.hora_entrada) BETWEEN '09:30:00' AND '09:50:00' THEN 'Café da Manhã'
                WHEN TIME(r.hora_entrada) BETWEEN '11:00:00' AND '12:50:00' THEN 'Almoço'
                WHEN TIME(r.hora_entrada) BETWEEN '14:30:00' AND '14:50:00' THEN 'Café da Tarde'
                WHEN TIME(r.hora_entrada) BETWEEN '19:30:00' AND '20:40:00' THEN 'Janta'
                ELSE 'Outros'
            END as turno
        FROM registros_refeitorio r
        JOIN alunos a ON r.aluno_id = a.id
        WHERE DATE(r.hora_entrada) = ?
        """
        
        params = [data]
        
        # Adicionar filtro de turnos se especificado
        if turno_conditions:
            query += " AND (" + " OR ".join(turno_conditions) + ")"
            params.extend(turno_params)
        
        query += " ORDER BY r.hora_entrada"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        registros = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        
        return registros
        
    except Exception as e:
        print(f'Erro ao gerar relatório diário: {e}')
        return []

def obter_estatisticas_gerais():
    """
    Retorna estatísticas gerais do sistema
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Total de alunos
        cursor.execute('SELECT COUNT(*) FROM alunos')
        total_alunos = cursor.fetchone()[0]
        
        # Total de registros hoje
        hoje = datetime.datetime.now().date()
        cursor.execute('SELECT COUNT(*) FROM registros_refeitorio WHERE DATE(hora_entrada) = ?', (hoje,))
        registros_hoje = cursor.fetchone()[0]
        
        # Total de registros este mês
        inicio_mes = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cursor.execute('SELECT COUNT(*) FROM registros_refeitorio WHERE hora_entrada >= ?', (inicio_mes,))
        registros_mes = cursor.fetchone()[0]
        
        # Alunos únicos hoje
        cursor.execute('SELECT COUNT(DISTINCT aluno_id) FROM registros_refeitorio WHERE DATE(hora_entrada) = ?', (hoje,))
        alunos_unicos_hoje = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'total_alunos': total_alunos,
            'registros_hoje': registros_hoje,
            'registros_mes': registros_mes,
            'alunos_unicos_hoje': alunos_unicos_hoje
        }
        
    except Exception as e:
        print(f'Erro ao obter estatísticas: {e}')
        return {}

def relatorio_por_periodo(data_inicio, data_fim, turnos_filtro=None):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Definindo os 4 turnos específicos
        cafe_manha_inicio = datetime.time(9, 30)
        cafe_manha_fim = datetime.time(9, 50)
        almoco_inicio = datetime.time(11, 0)
        almoco_fim = datetime.time(12, 50)
        cafe_tarde_inicio = datetime.time(14, 30)
        cafe_tarde_fim = datetime.time(14, 50)
        janta_inicio = datetime.time(19, 30)
        janta_fim = datetime.time(20, 40)
        
        # Construir filtro de turnos se especificado
        turno_conditions = []
        turno_params = []
        
        if turnos_filtro:
            for turno in turnos_filtro:
                if turno == 'Café da Manhã':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_manha_inicio, cafe_manha_fim])
                elif turno == 'Almoço':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([almoco_inicio, almoco_fim])
                elif turno == 'Café da Tarde':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([cafe_tarde_inicio, cafe_tarde_fim])
                elif turno == 'Janta':
                    turno_conditions.append("(TIME(hora_entrada) BETWEEN ? AND ?)")
                    turno_params.extend([janta_inicio, janta_fim])
        
        # Construir query base
        query = """
        SELECT 
            DATE(hora_entrada) as data,
            COUNT(*) as total_entradas,
            COUNT(DISTINCT aluno_id) as alunos_unicos
        FROM registros_refeitorio 
        WHERE DATE(hora_entrada) BETWEEN ? AND ?
        """
        
        params = [data_inicio, data_fim]
        
        # Adicionar filtro de turnos se especificado
        if turno_conditions:
            query += " AND (" + " OR ".join(turno_conditions) + ")"
            params.extend(turno_params)
        
        query += """
        GROUP BY DATE(hora_entrada)
        ORDER BY data
        """
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return resultados
        
    except Exception as e:
        print(f'Erro ao gerar relatório por período: {e}')
        return []