import mariadb
import datetime
import random
from db_utils import conectar_db

def adicionar_alunos_exemplo():
    """Adiciona alunos de exemplo ao banco de dados."""
    alunos = [
        (3781, "Kauã Gonçalves Pedrosa", "20212920043", "2003-01-30", "Bacharelado em Engenharia de Computação"),
        (1234, "Maria Silva Santos", "20212920044", "2002-05-15", "Bacharelado em Engenharia Civil"),
        (5678, "João Oliveira Costa", "20212920045", "2001-08-22", "Bacharelado em Engenharia Elétrica"),
        (9012, "Ana Paula Ferreira", "20212920046", "2002-12-10", "Bacharelado em Engenharia Mecânica"),
        (3456, "Carlos Eduardo Lima", "20212920047", "2001-03-18", "Bacharelado em Engenharia de Computação"),
        (7890, "Fernanda Rodrigues", "20212920048", "2002-07-25", "Bacharelado em Engenharia Civil"),
        (2345, "Lucas Mendes Alves", "20212920049", "2001-11-08", "Bacharelado em Engenharia Elétrica"),
        (6789, "Juliana Costa Silva", "20212920050", "2002-04-12", "Bacharelado em Engenharia Mecânica"),
        (4567, "Roberto Santos Oliveira", "20212920051", "2001-09-30", "Bacharelado em Engenharia de Computação"),
        (8901, "Patrícia Lima Ferreira", "20212920052", "2002-06-05", "Bacharelado em Engenharia Civil"),
        (3456, "Diego Alves Costa", "20212920053", "2001-02-14", "Bacharelado em Engenharia Elétrica"),
        (7890, "Camila Silva Mendes", "20212920054", "2002-10-20", "Bacharelado em Engenharia Mecânica"),
        (1235, "Gabriel Costa Santos", "20212920055", "2001-12-03", "Bacharelado em Engenharia de Computação"),
        (5679, "Isabela Ferreira Lima", "20212920056", "2002-01-28", "Bacharelado em Engenharia Civil"),
        (9013, "Thiago Oliveira Alves", "20212920057", "2001-07-17", "Bacharelado em Engenharia Elétrica"),
        (3457, "Amanda Santos Costa", "20212920058", "2002-03-09", "Bacharelado em Engenharia Mecânica"),
        (7891, "Rafael Lima Silva", "20212920059", "2001-05-25", "Bacharelado em Engenharia de Computação"),
        (2346, "Carolina Alves Ferreira", "20212920060", "2002-08-31", "Bacharelado em Engenharia Civil"),
        (6780, "Bruno Costa Mendes", "20212920061", "2001-04-07", "Bacharelado em Engenharia Elétrica"),
        (4568, "Larissa Silva Santos", "20212920062", "2002-11-15", "Bacharelado em Engenharia Mecânica")
    ]
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        for aluno in alunos:
            try:
                cursor.execute('''
                    INSERT INTO alunos (id, nome, matricula, data_nascimento, curso) 
                    VALUES (?, ?, ?, ?, ?)
                ''', aluno)
                print(f"Aluno adicionado: {aluno[1]}")
            except mariadb.IntegrityError:
                print(f"Aluno já existe: {aluno[1]}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Alunos adicionados com sucesso!")
        
    except Exception as e:
        print(f"Erro ao adicionar alunos: {e}")

def simular_entradas_refeitorio():
    """Simula entradas no refeitório em diferentes dias e turnos."""
    
    # Definir os turnos e seus horários
    turnos = {
        'Café da Manhã': (9, 30, 9, 50),  # 09:30-09:50
        'Almoço': (11, 0, 12, 50),        # 11:00-12:50
        'Café da Tarde': (14, 30, 14, 50), # 14:30-14:50
        'Janta': (19, 30, 20, 40)         # 19:30-20:40
    }
    
    # Datas para simular (últimos 7 dias)
    datas = []
    hoje = datetime.date.today()
    for i in range(7):
        data = hoje - datetime.timedelta(days=i)
        datas.append(data)
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Obter todos os alunos
        cursor.execute('SELECT id FROM alunos')
        alunos = [row[0] for row in cursor.fetchall()]
        
        if not alunos:
            print("Nenhum aluno encontrado. Execute primeiro adicionar_alunos_exemplo()")
            return
        
        registros_adicionados = 0
        
        for data in datas:
            print(f"\nSimulando entradas para {data.strftime('%d/%m/%Y')}:")
            
            for turno, (hora_inicio, min_inicio, hora_fim, min_fim) in turnos.items():
                # Determinar quantos alunos vão entrar neste turno (entre 3 e 8)
                num_alunos = random.randint(3, 8)
                alunos_turno = random.sample(alunos, min(num_alunos, len(alunos)))
                
                print(f"  {turno}: {len(alunos_turno)} alunos")
                
                for aluno_id in alunos_turno:
                    # Gerar hora aleatória dentro do turno
                    hora_entrada = random.randint(hora_inicio, hora_fim)
                    minuto_entrada = random.randint(0, 59)
                    
                    # Ajustar minutos se necessário
                    if hora_entrada == hora_inicio and minuto_entrada < min_inicio:
                        minuto_entrada = min_inicio
                    elif hora_entrada == hora_fim and minuto_entrada > min_fim:
                        minuto_entrada = min_fim
                    
                    # Criar datetime da entrada
                    entrada = datetime.datetime.combine(data, datetime.time(hora_entrada, minuto_entrada))
                    
                    # Gerar hora de saída (entre 30 minutos e 2 horas depois)
                    tempo_refeicao = random.randint(30, 120)  # minutos
                    saida = entrada + datetime.timedelta(minutes=tempo_refeicao)
                    
                    # Simular foto (BLOB vazio para simulação)
                    foto_simulada = b'foto_simulada'
                    
                    try:
                        cursor.execute('''
                            INSERT INTO registros_refeitorio (aluno_id, foto, hora_entrada, hora_saida) 
                            VALUES (?, ?, ?, ?)
                        ''', (aluno_id, foto_simulada, entrada, saida))
                        registros_adicionados += 1
                        
                    except mariadb.IntegrityError as e:
                        print(f"    Erro ao inserir registro: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\nSimulação concluída! {registros_adicionados} registros adicionados.")
        
    except Exception as e:
        print(f"Erro ao simular entradas: {e}")

def mostrar_estatisticas():
    """Mostra estatísticas dos dados inseridos."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Total de alunos
        cursor.execute('SELECT COUNT(*) FROM alunos')
        total_alunos = cursor.fetchone()[0]
        
        # Total de registros
        cursor.execute('SELECT COUNT(*) FROM registros_refeitorio')
        total_registros = cursor.fetchone()[0]
        
        # Registros por turno
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN TIME(hora_entrada) BETWEEN '09:30:00' AND '09:50:00' THEN 'Café da Manhã'
                    WHEN TIME(hora_entrada) BETWEEN '11:00:00' AND '12:50:00' THEN 'Almoço'
                    WHEN TIME(hora_entrada) BETWEEN '14:30:00' AND '14:50:00' THEN 'Café da Tarde'
                    WHEN TIME(hora_entrada) BETWEEN '19:30:00' AND '20:40:00' THEN 'Janta'
                    ELSE 'Outros'
                END as turno,
                COUNT(*) as total
            FROM registros_refeitorio 
            GROUP BY turno
            ORDER BY 
                CASE turno
                    WHEN 'Café da Manhã' THEN 1
                    WHEN 'Almoço' THEN 2
                    WHEN 'Café da Tarde' THEN 3
                    WHEN 'Janta' THEN 4
                    ELSE 5
                END
        ''')
        registros_por_turno = cursor.fetchall()
        
        # Registros por dia
        cursor.execute('''
            SELECT DATE(hora_entrada) as data, COUNT(*) as total
            FROM registros_refeitorio 
            GROUP BY DATE(hora_entrada)
            ORDER BY data DESC
        ''')
        registros_por_dia = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print("\n=== ESTATÍSTICAS DO BANCO ===")
        print(f"Total de alunos: {total_alunos}")
        print(f"Total de registros: {total_registros}")
        
        print("\nRegistros por turno:")
        for turno, total in registros_por_turno:
            print(f"  {turno}: {total} registros")
        
        print("\nRegistros por dia:")
        for data, total in registros_por_dia:
            print(f"  {data.strftime('%d/%m/%Y')}: {total} registros")
        
    except Exception as e:
        print(f"Erro ao mostrar estatísticas: {e}")

if __name__ == "__main__":
    print("=== POPULANDO BANCO DE DADOS ===")
    
    # 1. Adicionar alunos
    print("\n1. Adicionando alunos...")
    adicionar_alunos_exemplo()
    
    # 2. Simular entradas
    print("\n2. Simulando entradas no refeitório...")
    simular_entradas_refeitorio()
    
    # 3. Mostrar estatísticas
    print("\n3. Estatísticas finais:")
    mostrar_estatisticas()
    
    print("\n=== POPULAÇÃO CONCLUÍDA ===")
    print("Agora você pode testar os relatórios no sistema!") 