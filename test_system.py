#!/usr/bin/env python3
"""
Script de teste completo para o Sistema de Controle de Refeitório
Testa todas as funcionalidades principais do sistema
"""

import sys
import traceback
from datetime import datetime, timedelta
import mariadb

# Importar funções do sistema
try:
    from db_utils import (
        conectar_db, buscar_aluno_por_id, registrar_entrada_ou_saida,
        relatorio_entradas_por_turno, relatorio_semanal, relatorio_mensal,
        dados_grafico_frequencia_tempo, gerar_grafico_frequencia,
        obter_estatisticas_gerais
    )
    print("✅ Módulos do sistema importados com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

def test_conexao_banco():
    """Testa a conexão com o banco de dados"""
    print("\n🔍 Testando conexão com banco de dados...")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            print("✅ Conexão com banco de dados OK")
            return True
        else:
            print("❌ Conexão com banco falhou")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False

def test_estrutura_tabelas():
    """Testa se as tabelas necessárias existem"""
    print("\n🔍 Testando estrutura das tabelas...")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Verificar tabela alunos
        cursor.execute("SHOW TABLES LIKE 'alunos'")
        if not cursor.fetchone():
            print("❌ Tabela 'alunos' não encontrada")
            return False
        
        # Verificar tabela registros_refeitorio
        cursor.execute("SHOW TABLES LIKE 'registros_refeitorio'")
        if not cursor.fetchone():
            print("❌ Tabela 'registros_refeitorio' não encontrada")
            return False
        
        # Verificar colunas da tabela alunos
        cursor.execute("DESCRIBE alunos")
        colunas_alunos = [row[0] for row in cursor.fetchall()]
        colunas_esperadas = ['id', 'nome', 'matricula', 'data_nascimento', 'curso']
        
        for coluna in colunas_esperadas:
            if coluna not in colunas_alunos:
                print(f"❌ Coluna '{coluna}' não encontrada na tabela alunos")
                return False
        
        # Verificar colunas da tabela registros_refeitorio
        cursor.execute("DESCRIBE registros_refeitorio")
        colunas_registros = [row[0] for row in cursor.fetchall()]
        colunas_esperadas_reg = ['id', 'aluno_id', 'foto', 'hora_entrada', 'hora_saida']
        
        for coluna in colunas_esperadas_reg:
            if coluna not in colunas_registros:
                print(f"❌ Coluna '{coluna}' não encontrada na tabela registros_refeitorio")
                return False
        
        cursor.close()
        conn.close()
        print("✅ Estrutura das tabelas OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura das tabelas: {e}")
        return False

def test_dados_alunos():
    """Testa se existem dados de alunos no banco"""
    print("\n🔍 Testando dados de alunos...")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM alunos")
        total_alunos = cursor.fetchone()[0]
        
        if total_alunos > 0:
            print(f"✅ Encontrados {total_alunos} alunos no banco")
            
            # Testar busca de aluno
            cursor.execute("SELECT id FROM alunos LIMIT 1")
            aluno_id = cursor.fetchone()[0]
            
            aluno = buscar_aluno_por_id(str(aluno_id))
            if aluno:
                print(f"✅ Busca de aluno OK - Nome: {aluno.get('nome', 'N/A')}")
            else:
                print("❌ Erro na busca de aluno")
                return False
        else:
            print("⚠️  Nenhum aluno cadastrado no banco")
            print("   Para testar completamente, adicione alguns alunos:")
            print("   INSERT INTO alunos (nome, matricula, data_nascimento, curso) VALUES")
            print("   ('João Silva', '2023001', '2000-01-01', 'Informática'),")
            print("   ('Maria Santos', '2023002', '1999-05-15', 'Administração');")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar dados de alunos: {e}")
        return False

def test_relatorios():
    """Testa as funções de relatórios"""
    print("\n🔍 Testando funções de relatórios...")
    
    try:
        # Teste relatório por turno
        resultados_turno = relatorio_entradas_por_turno()
        print(f"✅ Relatório por turno: {len(resultados_turno)} registros encontrados")
        
        # Teste relatório semanal
        resultados_semanal = relatorio_semanal()
        print(f"✅ Relatório semanal: {len(resultados_semanal)} registros encontrados")
        
        # Teste relatório mensal
        resultados_mensal = relatorio_mensal()
        print(f"✅ Relatório mensal: {len(resultados_mensal)} registros encontrados")
        
        # Teste dados para gráfico
        dados_grafico = dados_grafico_frequencia_tempo()
        print(f"✅ Dados para gráfico: {len(dados_grafico)} registros encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar relatórios: {e}")
        return False

def test_estatisticas():
    """Testa as funções de estatísticas"""
    print("\n🔍 Testando funções de estatísticas...")
    
    try:
        stats = obter_estatisticas_gerais()
        
        if isinstance(stats, dict):
            print("✅ Estatísticas geradas com sucesso:")
            print(f"   - Total de alunos: {stats.get('total_alunos', 0)}")
            print(f"   - Registros hoje: {stats.get('registros_hoje', 0)}")
            print(f"   - Registros mês: {stats.get('registros_mes', 0)}")
            print(f"   - Alunos únicos hoje: {stats.get('alunos_unicos_hoje', 0)}")
            return True
        else:
            print("❌ Erro ao gerar estatísticas")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar estatísticas: {e}")
        return False

def test_grafico():
    """Testa a geração de gráficos"""
    print("\n🔍 Testando geração de gráficos...")
    
    try:
        # Teste geração de gráfico
        sucesso = gerar_grafico_frequencia()
        
        if sucesso:
            print("✅ Gráfico gerado com sucesso")
            print("   Verifique o arquivo 'grafico_frequencia.png'")
        else:
            print("⚠️  Nenhum dado encontrado para gerar gráfico")
            print("   Isso é normal se não houver registros no período")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar gráficos: {e}")
        return False

def test_dependencias():
    """Testa se todas as dependências estão instaladas"""
    print("\n🔍 Testando dependências...")
    
    dependencias = [
        ('cv2', 'OpenCV'),
        ('PyQt5', 'PyQt5'),
        ('pyzbar', 'pyzbar'),
        ('PIL', 'Pillow'),
        ('mariadb', 'mariadb'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('matplotlib', 'matplotlib')
    ]
    
    todas_ok = True
    
    for modulo, nome in dependencias:
        try:
            __import__(modulo)
            print(f"✅ {nome} - OK")
        except ImportError:
            print(f"❌ {nome} - FALTANDO")
            todas_ok = False
    
    return todas_ok

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do Sistema de Controle de Refeitório")
    print("=" * 60)
    
    testes = [
        ("Dependências", test_dependencias),
        ("Conexão com Banco", test_conexao_banco),
        ("Estrutura das Tabelas", test_estrutura_tabelas),
        ("Dados de Alunos", test_dados_alunos),
        ("Relatórios", test_relatorios),
        ("Estatísticas", test_estatisticas),
        ("Gráficos", test_grafico)
    ]
    
    resultados = []
    
    for nome, teste in testes:
        try:
            resultado = teste()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ Erro inesperado no teste '{nome}': {e}")
            resultados.append((nome, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    total_tests = len(resultados)
    testes_ok = sum(1 for _, resultado in resultados if resultado)
    
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{nome:.<30} {status}")
    
    print("-" * 60)
    print(f"Total de testes: {total_tests}")
    print(f"Testes aprovados: {testes_ok}")
    print(f"Testes reprovados: {total_tests - testes_ok}")
    
    if testes_ok == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
    else:
        print(f"\n⚠️  {total_tests - testes_ok} teste(s) falharam. Verifique os problemas acima.")
    
    print("\n💡 Dicas:")
    print("   - Se a conexão com banco falhou, verifique as credenciais em db_utils.py")
    print("   - Se dependências estão faltando, execute: pip install -r requirements.txt")
    print("   - Se tabelas não existem, execute: mysql -u root -p < db_setup.sql")
    print("   - Para adicionar alunos de teste, use os comandos SQL mostrados acima")

if __name__ == "__main__":
    main() 