# 🍽️ Sistema de Controle de Refeitório - IFF

> Sistema inteligente para controle de entrada e saída de alunos no refeitório do Instituto Federal Fluminense

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15.9-green.svg)](https://pypi.org/project/PyQt5/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.12.0-orange.svg)](https://opencv.org)
[![MariaDB](https://img.shields.io/badge/MariaDB-1.1.13-red.svg)](https://mariadb.org)

## 🎯 O que é?

Um sistema desktop completo que automatiza o controle de acesso ao refeitório usando **códigos de barras** e **detecção  facial**. Os alunos simplesmente aproximam seus cartões da câmera e posicionam o rosto na área demarcada - o sistema faz todo o resto automaticamente! 🚀

## ✨ Funcionalidades Principais

### 🎫 **Controle Automático**
- **Leitura de Código de Barras**: Captura instantânea de códigos Code 128 dos cartões dos alunos
- **Detecção Facial Inteligente**: Overlay oval que guia o posicionamento do rosto
- **Captura Automática**: Foto tirada automaticamente quando o rosto está centralizado
- **Registro Inteligente**: Sistema detecta se é entrada ou saída automaticamente

### 📊 **Relatórios Detalhados**
- **Relatório Diário**: Frequência do dia com filtros por turno
- **Relatório por Período**: Escolha datas personalizadas
- **Relatório por Turnos**: 
  - ☕ Café da manhã (09:30-09:50)
  - 🍽️ Almoço (11:00-12:50)
  - 🍰 Café da tarde (14:30-14:50)
  - 🍽️ Janta (19:30-20:40)

### 📈 **Gráficos Visuais**
- **Gráficos de Frequência**: Visualização interativa da frequência por hora/dia
- **Múltiplos Períodos**: Últimas 24h, 7 dias, 30 dias, etc.
- **Janela Separada**: Gráficos em janela dedicada para melhor visualização

### 🎨 **Interface Moderna**
- **Design Clean**: Interface verde com logo do IFF
- **Sistema de Abas**: Organização clara das funcionalidades
- **Feedback Visual**: Status coloridos e mensagens informativas
- **Responsivo**: Adapta-se a diferentes resoluções

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Função |
|------------|--------|--------|
| **Python** | 3.8+ | Linguagem principal |
| **PyQt5** | 5.15.9 | Interface gráfica moderna |
| **OpenCV** | 4.12.0.88 | Captura de vídeo e detecção facial |
| **pyzbar** | 0.1.9 | Leitura de códigos de barras |
| **MariaDB** | 1.1.13 | Banco de dados |
| **Matplotlib** | 3.10.5 | Geração de gráficos |
| **Pandas** | 2.3.1 | Manipulação de dados |
| **Pillow** | 11.3.0 | Processamento de imagens |
| **NumPy** | 2.2.6 | Operações numéricas |

## 🚀 Instalação Rápida

### 📋 Pré-requisitos
- ✅ Python 3.8 ou superior
- ✅ MariaDB/MySQL instalado
- ✅ Webcam funcional
- ✅ Windows 10/11

### ⚡ Instalação Automática (Windows)

1. **Clone o repositório**
   ```bash
   git clone <https://github.com/MV4rg4s/ControleRefeitorio>
   cd ControleRefeitorio
   ```

2. **Execute o script de instalação**
   ```bash
   install_dependencies.bat
   ```

3. **Configure o banco de dados**
   - Abra o HeidiSQL ou MySQL Workbench
   - Execute o script `db_setup.sql`
   - Ajuste as credenciais em `db_utils.py` se necessário

4. **Execute o sistema**
   ```bash
   python main.py
   ```

### 🔧 Instalação Manual

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar sistema
python main.py
```

## 🗄️ Estrutura do Banco de Dados

### 📚 Tabela `alunos`
```sql
CREATE TABLE alunos (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- ID único do aluno
    nome VARCHAR(255) NOT NULL,               -- Nome completo
    matricula VARCHAR(50) NOT NULL UNIQUE,    -- Matrícula acadêmica
    data_nascimento DATE NOT NULL,            -- Data de nascimento
    curso VARCHAR(100) NOT NULL               -- Curso do aluno
);
```

### 📝 Tabela `registros_refeitorio`
```sql
CREATE TABLE registros_refeitorio (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- ID do registro
    aluno_id INT NOT NULL,                    -- Referência ao aluno
    foto LONGBLOB,                            -- Foto capturada (BLOB)
    hora_entrada DATETIME,                    -- Horário de entrada
    hora_saida DATETIME,                      -- Horário de saída
    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
);
```

## 🎮 Como Usar

### 🎯 **Controle Principal**
1. **Abra o sistema** - A câmera será ativada automaticamente
2. **Aproxime o cartão** - Posicione o código de barras na frente da câmera
3. **Aguarde a leitura** - O sistema identificará o aluno automaticamente
4. **Posicione o rosto** - Encaixe o rosto na área oval verde
5. **Foto automática** - O sistema capturará a foto quando centralizado
6. **Registro completo** - Entrada ou saída será registrada automaticamente

### 📊 **Geração de Relatórios**
1. **Acesse a aba "Relatórios"**
2. **Escolha o tipo**:
   - **Relatório Rápido**: Dados do dia atual
   - **Relatório Diário**: Data específica com filtros
   - **Relatório por Período**: Intervalo personalizado
3. **Selecione os turnos** (opcional): Marque os turnos desejados
4. **Clique em gerar** - Os dados aparecerão na tabela

### 📈 **Visualização de Gráficos**
1. **Acesse a aba "Gráficos"**
2. **Escolha o período**: Últimas 24h, 7 dias, 30 dias, etc.
3. **Clique em "Gerar Gráfico"**
4. **Visualize**: O gráfico abrirá em uma janela separada

## 📁 Estrutura do Projeto

```
ControleRefeitorio/
├── 🎯 main.py                 # Aplicação principal
├── 🗄️ db_utils.py            # Funções do banco de dados
├── 👤 face_overlay.py        # Detecção facial e overlay
├── 📊 populate_database.py   # Script para dados de teste
├── ⚙️ db_setup.sql          # Criação das tabelas
├── 📦 requirements.txt       # Dependências Python
├── 🚀 install_dependencies.bat # Instalação automática
├── 🏫 logo_iff.png          # Logo da instituição
└── 📖 README.md             # Esta documentação
```

## ⚙️ Configurações

### 🕐 **Horários dos Turnos**
Os horários podem ser ajustados em `db_utils.py`:

```python
# Turnos configuráveis
TURNOS = {
    "cafe_da_manha": ("09:30", "09:50"),
    "almoco": ("11:00", "12:50"),
    "cafe_da_tarde": ("14:30", "14:50"),
    "janta": ("19:30", "20:40")
}
```

### 📷 **Configurações de Câmera**
```python
# Para usar câmera diferente
self.cap = cv2.VideoCapture(1)  # Segunda câmera
```

### 🗄️ **Configurações do Banco**
```python
# Em db_utils.py
def conectar_db():
    return mariadb.connect(
        host='localhost',
        user='root',
        password='sua_senha',
        database='controle_refeitorio'
    )
```

## 🔧 Solução de Problemas

### ❌ **Câmera não funciona**
- ✅ Verifique se a webcam está conectada
- ✅ Teste com outro aplicativo
- ✅ Verifique permissões do Windows

### ❌ **Código de barras não lê**
- ✅ Melhore a iluminação
- ✅ Aproxime mais o cartão
- ✅ Limpe a lente da câmera

### ❌ **Erro de banco de dados**
- ✅ Verifique se o MariaDB está rodando
- ✅ Confirme as credenciais em `db_utils.py`
- ✅ Execute o script `db_setup.sql`

### ❌ **Dependências não instalam**
- ✅ Execute `install_dependencies.bat`
- ✅ Atualize o pip: `pip install --upgrade pip`
- ✅ Use ambiente virtual se necessário

## 🆕 Funcionalidades Recentes

### ✅ **v3.0 - Gráficos Visuais**
- Gráficos de barras interativos
- Múltiplos períodos de análise
- Janela separada para visualização
- Cores e estilos modernos

### ✅ **v2.0 - Relatórios Avançados**
- Relatório por período personalizado
- Filtros por turnos
- 4 turnos configurados
- Interface melhorada

### ✅ **v1.0 - Controle Básico**
- Leitura de código de barras
- Detecção facial
- Registro automático
- Interface PyQt5

## 📞 Contato

- **Matheus Vargas**: 📱 (22) 98848-4742  
- **Arthur Miguelito**: 📱 (22) 99971-1856

## 📄 Licença

Desenvolvido para o **Instituto Federal Fluminense (IFF)**.

---

<div align="center">

**🍽️ Sistema de Controle de Refeitório - IFF**

*Desenvolvido com ❤️ para a comunidade acadêmica*

[![IFF](https://img.shields.io/badge/IFF-Instituto%20Federal%20Fluminense-blue.svg)](https://iff.edu.br)

</div>


