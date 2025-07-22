import mysql.connector
import sys
import traceback

def conectar_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='123',  # Altere para sua senha
        database='controle_refeitorio'
    )

def buscar_aluno_por_matricula(matricula):
    try:
        id_int = int(matricula)
        print(f'Consultando aluno com ID: {id_int}')
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM alunos WHERE id = %s', (id_int,))
        aluno = cursor.fetchone()
        print(f'Resultado da consulta: {aluno}')
        cursor.close()
        conn.close()
        return aluno
    except Exception as e:
        print(f'Erro ao consultar aluno: {e}')
        return None 

def excecao_nao_tratada(exctype, value, tb):
    print("Exceção não tratada:", exctype, value)
    traceback.print_tb(tb)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = excecao_nao_tratada 