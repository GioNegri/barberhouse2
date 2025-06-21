import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
def conectar():
    conn = sqlite3.connect('barbearia.db')
    return conn
def atualizar_tabela_agendamentos():
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(agendamentos)')
        colunas = [info[1] for info in cursor.fetchall()] 
        if 'status' not in colunas:
            cursor.execute('ALTER TABLE agendamentos ADD COLUMN status TEXT NOT NULL DEFAULT "pendente"')
            conn.commit()
            print("Coluna 'status' adicionada à tabela 'agendamentos'.")
    except Exception as e:
        print(f"Erro ao atualizar tabela: {e}")
    finally:
        conn.close()
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        sobrenome TEXT NOT NULL        
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL
    )
    ''')  
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS barbeiros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    ''')  
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        servico_id INTEGER NOT NULL,
        barbeiro_id INTEGER NOT NULL,
        data_hora TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pendente', 'concluido', 'cancelado')),
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(servico_id) REFERENCES servicos(id),
        FOREIGN KEY(barbeiro_id) REFERENCES barbeiros(id)
    )
    ''')
    conn.commit()
    conn.close()
def cadastrar_cliente(nome, sobrenome):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO clientes (nome, sobrenome) VALUES (?, ?)', (nome, sobrenome))
        conn.commit()
        cliente_id = cursor.lastrowid
        print("Cliente cadastrado com sucesso!")
        return cliente_id  
    except Exception as e:
        print(f"Erro ao cadastrar cliente: {e}")
        return None
    finally:
        conn.close()
def cadastrar_servico(nome, preco):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO servicos (nome, preco) VALUES (?, ?)', (nome, preco))
    conn.commit()
    conn.close()
def cadastrar_barbeiro(nome):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO barbeiros (nome) VALUES (?)', (nome,))
        conn.commit()
        print("Barbeiro cadastrado com sucesso!")
    except Exception as e:
        print(f"Erro ao cadastrar barbeiro: {e}")
    finally:
        conn.close()
def agendar_horario(cliente_id, servico_id, barbeiro_id, data_hora):
    conn = conectar()
    cursor = conn.cursor()
    try:    
        cursor.execute('SELECT id FROM clientes WHERE id = ?', (cliente_id,))
        if not cursor.fetchone():
            print("Erro: Cliente não encontrado.")
            return False
        
        cursor.execute('SELECT id FROM servicos WHERE id = ?', (servico_id,))
        if not cursor.fetchone():
            print("Erro: Serviço não encontrado.")
            return False

        cursor.execute('SELECT id FROM barbeiros WHERE id = ?', (barbeiro_id,))
        if not cursor.fetchone():
            print("Erro: Barbeiro não encontrado.")
            return False 
        
        cursor.execute('SELECT * FROM agendamentos WHERE data_hora = ? AND status != "cancelado"', (data_hora,))
        if cursor.fetchone():
            print("Erro: Horário indisponível.")
            return False
            
        cursor.execute('INSERT INTO agendamentos (cliente_id, servico_id, barbeiro_id, data_hora, status) VALUES (?, ?, ?, ?, ?)', 
                      (cliente_id, servico_id, barbeiro_id, data_hora, 'pendente'))
        conn.commit()
        print("Agendamento confirmado!")
        return True
    except Exception as e:
        print(f"Erro ao agendar: {e}")
        return False
    finally:
        conn.close()

def atualizar_status_agendamento(agendamento_id, novo_status):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE agendamentos SET status = ? WHERE id = ?', (novo_status, agendamento_id))
        conn.commit()
        print(f"Status do agendamento {agendamento_id} atualizado para '{novo_status}'.")
        return True
    except Exception as e:
        print(f"Erro ao atualizar status: {e}")
        return False
    finally:
        conn.close()
def listar_servicos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, preco FROM servicos')
    servicos = cursor.fetchall()
    conn.close()
    return servicos

def listar_barbeiros():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome FROM barbeiros')
    barbeiros = cursor.fetchall()
    conn.close()
    return barbeiros
def listar_agendamentos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT a.id, c.nome,  s.nome, s.preco, a.data_hora, a.status
    FROM agendamentos a
    JOIN clientes c ON a.cliente_id = c.id
    JOIN servicos s ON a.servico_id = s.id
    ''')
    agendamentos = cursor.fetchall()
    conn.close()
    return agendamentos

def listar_agendamentos_com_barbeiro():
    conn = sqlite3.connect('barbearia.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ag.id, c.nome, s.nome, ag.data_hora, ag.status, b.nome
        FROM agendamentos ag
        JOIN clientes c ON ag.cliente_id = c.id
        JOIN servicos s ON ag.servico_id = s.id
        JOIN barbeiros b ON ag.barbeiro_id = b.id
    """)
    resultados = cursor.fetchall()
    conn.close()
    return resultados
def listar_agendamentos_com_valores():
    conn = sqlite3.connect('barbearia.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nome, s.preco, DATE(ag.data_hora), ag.status
        FROM agendamentos ag
        JOIN servicos s ON ag.servico_id = s.id
    """)
    resultados = cursor.fetchall()
    conn.close()
    return resultados
def gerar_dados_relatorio_detalhado():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, c.nome, s.nome, a.data_hora, a.status
        FROM agendamentos a
        JOIN clientes c ON a.cliente_id = c.id
        JOIN servicos s ON a.servico_id = s.id
        ORDER BY a.data_hora
    """)
    dados = cursor.fetchall()
    conn.close()
    return pd.DataFrame(dados, columns=["ID", "Cliente", "Serviço", "Data e Hora", "Status"])
def gerar_dados_relatorio_por_servico():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nome, a.status, COUNT(*) as quantidade
        FROM agendamentos a
        JOIN servicos s ON a.servico_id = s.id
        GROUP BY s.nome, a.status
        ORDER BY s.nome
    """)
    dados = cursor.fetchall()
    conn.close()
    return pd.DataFrame(dados, columns=["Serviço", "Status", "Quantidade"])
def gerar_dados_relatorio_por_barbeiro():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.nome, COUNT(*) as total_atendimentos
        FROM agendamentos a
        JOIN barbeiros b ON a.barbeiro_id = b.id
        WHERE a.status = 'concluido'
        GROUP BY b.nome
        ORDER BY total_atendimentos DESC
    """)
    dados = cursor.fetchall()
    conn.close()
    return pd.DataFrame(dados, columns=["Barbeiro", "Total de Atendimentos"])
def gerar_dados_relatorio_mensal_recebimentos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT STRFTIME('%Y-%m', a.data_hora) AS mes, SUM(s.preco) AS total
        FROM agendamentos a
        JOIN servicos s ON a.servico_id = s.id
        WHERE a.status = 'concluido'
        GROUP BY mes
        ORDER BY mes
    """)
    dados = cursor.fetchall()
    conn.close()
    return pd.DataFrame(dados, columns=['Mês', 'Total Recebido'])