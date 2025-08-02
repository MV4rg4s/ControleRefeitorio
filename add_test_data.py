#!/usr/bin/env python3
"""
Script para adicionar dados de teste ao banco de dados
Útil para testar as funcionalidades do sistema
"""

import sys
from datetime import datetime, timedelta
import random
from db_utils import conectar_db

def adicionar_alunos_teste():
    """Adiciona alunos de teste ao banco"""
    print("📝 Adicionando alunos de teste...")
    
    alunos_teste = [
        ('João Silva', '2023001', '2000-01-15', 'Informática'),
        ('Maria Santos', '2023002', '1999-05-20', 'Administração'),
        ('Pedro Oliveira', '2023003', '2001-03-10', 'Engenharia'),
        ('Ana Costa', '2023004', '2000-08-25', 'Informática'),
        ('Carlos Ferreira', '2023005', '1998-12-05', 'Administração'),
        ('Lucia Pereira', '2023006', '2002-07-18', 'Engenharia'),
        ('Roberto Lima', '2023007', '1999-11-30', 'Informática'),
        ('Fernanda Rocha', '2023008', '2000-04-12', 'Administração'),
        ('Diego Almeida', '2023009', '2001-09-08', 'Engenharia'),
        ('Camila Souza', '2023010', '1998-06-22', 'Informática')
    ]
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Verificar se já existem alunos
        cursor.execute("SELECT COUNT(*) FROM alunos")
        total_existente = cursor.fetchone()[0]
        
        if total_existente > 0:
            print(f"⚠️  Já existem {total_existente} alunos no banco")
            resposta = input("Deseja adicionar mais alunos? (s/n): ").lower()
            if resposta != 's':
                print("Operação cancelada")
                return
        
        # Adicionar alunos
        for nome, matricula, data_nasc, curso in alunos_teste:
            try:
                cursor.execute("""
                    INSERT INTO alunos (nome, matricula, data_nascimento, curso) 
                    VALUES (?, ?, ?, ?)
                """, (nome, matricula, data_nasc, curso))
                print(f"✅ Adicionado: {nome} - {matricula}")
            except Exception as e:
                if "Duplicate entry" in str(e):
                    print(f"⚠️  Aluno já existe: {nome}")
                else:
                    print(f"❌ Erro ao adicionar {nome}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✅ {len(alunos_teste)} alunos adicionados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar alunos: {e}")

def adicionar_registros_teste():
    """Adiciona registros de teste ao banco"""
    print("\n📝 Adicionando registros de teste...")
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Verificar se existem alunos
        cursor.execute("SELECT id FROM alunos LIMIT 5")
        alunos = cursor.fetchall()
        
        if not alunos:
            print("❌ Nenhum aluno encontrado. Execute primeiro: add_test_data.py")
            return
        
        # Gerar registros para os últimos 7 dias
        hoje = datetime.now()
        registros_adicionados = 0
        
        for dias_atras in range(7):
            data = hoje - timedelta(days=dias_atras)
            
            # Gerar registros para cada dia
            for aluno_id in [aluno[0] for aluno in alunos]:
                # 70% de chance de ter registro no dia
                if random.random() < 0.7:
                    # Gerar horário de entrada (entre 10:30 e 14:30 ou 17:30 e 20:30)
                    if random.random() < 0.6:  # 60% almoço
                        hora_entrada = data.replace(
                            hour=random.randint(10, 14),
                            minute=random.randint(0, 59)
                        )
                    else:  # 40% janta
                        hora_entrada = data.replace(
                            hour=random.randint(17, 20),
                            minute=random.randint(0, 59)
                        )
                    
                    # 80% de chance de ter saída
                    if random.random() < 0.8:
                        hora_saida = hora_entrada + timedelta(
                            hours=random.randint(1, 3),
                            minutes=random.randint(0, 59)
                        )
                    else:
                        hora_saida = None
                    
                    try:
                        cursor.execute("""
                            INSERT INTO registros_refeitorio 
                            (aluno_id, hora_entrada, hora_saida) 
                            VALUES (?, ?, ?)
                        """, (aluno_id, hora_entrada, hora_saida))
                        registros_adicionados += 1
                    except Exception as e:
                        print(f"❌ Erro ao adicionar registro: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ {registros_adicionados} registros adicionados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar registros: {e}")

def mostrar_estatisticas():
    """Mostra estatísticas dos dados no banco"""
    print("\n📊 Estatísticas dos dados:")
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Total de alunos
        cursor.execute("SELECT COUNT(*) FROM alunos")
        total_alunos = cursor.fetchone()[0]
        print(f"👥 Total de alunos: {total_alunos}")
        
        # Total de registros
        cursor.execute("SELECT COUNT(*) FROM registros_refeitorio")
        total_registros = cursor.fetchone()[0]
        print(f"📝 Total de registros: {total_registros}")
        
        # Registros hoje
        hoje = datetime.now().date()
        cursor.execute("SELECT COUNT(*) FROM registros_refeitorio WHERE DATE(hora_entrada) = %s", (hoje,))
        registros_hoje = cursor.fetchone()[0]
        print(f"📅 Registros hoje: {registros_hoje}")
        
        # Registros por curso
        cursor.execute("""
            SELECT a.curso, COUNT(r.id) as total
            FROM alunos a
            LEFT JOIN registros_refeitorio r ON a.id = r.aluno_id
            GROUP BY a.curso
            ORDER BY total DESC
        """)
        cursos = cursor.fetchall()
        print("\n📚 Registros por curso:")
        for curso, total in cursos:
            print(f"   {curso}: {total} registros")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao mostrar estatísticas: {e}")

def main():
    """Função principal"""
    print("🚀 Adicionando dados de teste ao Sistema de Controle de Refeitório")
    print("=" * 60)
    
    while True:
        print("\nEscolha uma opção:")
        print("1. Adicionar alunos de teste")
        print("2. Adicionar registros de teste")
        print("3. Mostrar estatísticas")
        print("4. Executar tudo")
        print("5. Sair")
        
        opcao = input("\nDigite sua opção (1-5): ").strip()
        
        if opcao == "1":
            adicionar_alunos_teste()
        elif opcao == "2":
            adicionar_registros_teste()
        elif opcao == "3":
            mostrar_estatisticas()
        elif opcao == "4":
            adicionar_alunos_teste()
            adicionar_registros_teste()
            mostrar_estatisticas()
            print("\n✅ Todos os dados de teste foram adicionados!")
        elif opcao == "5":
            print("👋 Saindo...")
            break
        else:
            print("❌ Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main() 