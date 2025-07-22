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
        # Não tem entrada aberta, registrar nova entrada
        cursor.execute('INSERT INTO registros_refeitorio (aluno_id, foto, hora_entrada) VALUES (?, ?, ?)',
                       (aluno_id, foto_bytes, agora))
        conn.commit()
        cursor.close()
        conn.close()
        return 'entrada', agora