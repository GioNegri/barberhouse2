import tkinter as tk
import pandas as pd
import openpyxl
from openpyxl.chart import BarChart, Reference, PieChart
import matplotlib.pyplot as plt
import os
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from database import conectar, cadastrar_cliente, cadastrar_servico, criar_tabelas, listar_servicos, listar_agendamentos, agendar_horario, atualizar_status_agendamento, cadastrar_barbeiro
from tkcalendar import DateEntry
from datetime import datetime
from database import (
    gerar_dados_relatorio_detalhado,
    gerar_dados_relatorio_por_servico,
    gerar_dados_relatorio_por_barbeiro,
    gerar_dados_relatorio_mensal_recebimentos
)


# Funções de cada botão

def cadastrar_cliente_janela():
    cadastro_window = tk.Toplevel()
    cadastro_window.title("Cadastrar Cliente")

    tk.Label(cadastro_window, text="Nome Completo:").pack()
    nome_entry = tk.Entry(cadastro_window)
    nome_entry.pack()

    tk.Label(cadastro_window, text="Telefone:").pack()
    telefone_entry = tk.Entry(cadastro_window)
    telefone_entry.pack()

    def confirmar_cadastro():
        nome = nome_entry.get()
        telefone = telefone_entry.get()
        if nome and telefone:
            cliente_id = cadastrar_cliente(nome, telefone)
            if cliente_id:
                msg = f"Cliente cadastrado com sucesso!\nID: {cliente_id}"
                tk.Label(cadastro_window, text=msg, fg="green", font=("Arial", 12, "bold")).pack(pady=10)
            else:
                messagebox.showerror("Erro", "Falha ao cadastrar cliente.")

    tk.Button(cadastro_window, text="Confirmar", command=confirmar_cadastro).pack(pady=10)

def cadastrar_servico_janela():
    servico_window = tk.Toplevel()
    servico_window.title("Cadastrar Serviço")

    tk.Label(servico_window, text="Nome do Serviço:").pack()
    nome_entry = tk.Entry(servico_window)
    nome_entry.pack()

    tk.Label(servico_window, text="Preço:").pack()
    preco_entry = tk.Entry(servico_window)
    preco_entry.pack()

    def confirmar_cadastro():
        nome = nome_entry.get()
        preco = preco_entry.get()
        if nome and preco:
            try:
                preco = float(preco)
            except ValueError:
                messagebox.showerror("Erro", "Preço deve ser um número!")
                return

            cadastrar_servico(nome, preco)
            messagebox.showinfo("Sucesso", "Serviço cadastrado!")
            servico_window.destroy()
        else:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos!")

    tk.Button(servico_window, text="Confirmar", command=confirmar_cadastro).pack(pady=10)

def listar_agendamentos_janela():
    listar_window = tk.Toplevel()
    listar_window.title("Agendamentos")

    tree = ttk.Treeview(listar_window, columns=("ID", "Cliente", "Serviço","Preço", "DataHora", "Status"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Cliente", text="Cliente")
    tree.heading("Serviço", text="Serviço")
    tree.heading("Preço", text="Preço")
    tree.heading("DataHora", text="Data e Hora")
    tree.heading("Status", text="Status")

    tree.pack(fill="both", expand=True)

    agendamentos = listar_agendamentos()
    for agendamento in agendamentos:
        tree.insert("", "end", values=agendamento)

def agendar_horario_janela():
    agendar_window = tk.Toplevel()
    agendar_window.title("Agendar Horário")

    tk.Label(agendar_window, text="ID do Cliente:").pack()
    cliente_id_entry = tk.Entry(agendar_window)
    cliente_id_entry.pack()

    # Serviços disponíveis
    servicos = listar_servicos()
    if not servicos:
        tk.Label(agendar_window, text="Nenhum serviço cadastrado.").pack()
        return

    tk.Label(agendar_window, text="Escolha o Serviço:").pack()
    servico_var = tk.StringVar()
    servico_combobox = ttk.Combobox(agendar_window, textvariable=servico_var, state="readonly", width=50)
    servico_combobox.pack()

    servico_id_map = {}
    servico_display_list = []
    for servico in servicos:
        display = f"{servico[1]} (R${servico[2]:.2f})"
        servico_display_list.append(display)
        servico_id_map[display] = servico[0]
    servico_combobox['values'] = servico_display_list

    # Barbeiros disponíveis
    from database import listar_barbeiros
    barbeiros = listar_barbeiros()
    if not barbeiros:
        tk.Label(agendar_window, text="Nenhum barbeiro cadastrado.").pack()
        return

    tk.Label(agendar_window, text="Escolha o Barbeiro:").pack()
    barbeiro_var = tk.StringVar()
    barbeiro_combobox = ttk.Combobox(agendar_window, textvariable=barbeiro_var, state="readonly", width=50)
    barbeiro_combobox.pack()

    barbeiro_id_map = {}
    barbeiro_display_list = []
    for barbeiro in barbeiros:
        display = f"{barbeiro[1]} (ID: {barbeiro[0]})"
        barbeiro_display_list.append(display)
        barbeiro_id_map[display] = barbeiro[0]
    barbeiro_combobox['values'] = barbeiro_display_list

    
    tk.Label(agendar_window, text="Data e Hora (DD/MM/AAAA HH:MM):").pack()
    data_hora_entry = tk.Entry(agendar_window)
    data_hora_entry.pack()

    def confirmar_agendamento():
        cliente_id = cliente_id_entry.get()
        servico_display = servico_var.get()
        barbeiro_display = barbeiro_var.get()
        data_hora = data_hora_entry.get()

        if not cliente_id or not servico_display or not barbeiro_display or not data_hora:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos!")
            return

        try:
            data_hora_obj = datetime.strptime(data_hora, "%d/%m/%Y %H:%M")
        except ValueError:
            messagebox.showerror("Erro", "Formato de data/hora inválido. Use DD/MM/AAAA HH:MM.")
            return
        
        dia_semana = data_hora_obj.weekday()
        hora = data_hora_obj.hour
        minuto=data_hora_obj.minute
        
        permitido = False 
        if dia_semana == 5:  # Sábado
            permitido = (hora < 17) or (hora == 17 and minuto <= 30)
        elif dia_semana in [1, 2, 3, 4]:  # Terça a sexta
            permitido = (hora < 19) or (hora == 19 and minuto <= 30)
        else:   
            permitido = False

        if not permitido:
            messagebox.showerror("Horário inválido", "Agendamentos permitidos apenas:\n"
            "- Terça a sexta: 09:00 às 20:00\n"
            "- Sábado: 09:00 às 18:00\n"
            "Domingo e segunda: Fechado.")
            return

        servico_id = servico_id_map.get(servico_display)
        barbeiro_id = barbeiro_id_map.get(barbeiro_display)

        sucesso = agendar_horario(int(cliente_id), servico_id, barbeiro_id, data_hora_obj.strftime("%Y-%m-%d %H:%M"))
        if sucesso:
            messagebox.showinfo("Sucesso", "Agendamento realizado!")
            agendar_window.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao agendar. Verifique as informações.")

    tk.Button(agendar_window, text="Confirmar Agendamento", command=confirmar_agendamento).pack(pady=10)

def atualizar_status_janela():
    atualizar_window = tk.Toplevel()
    atualizar_window.title("Atualizar Status do Agendamento")

    tk.Label(atualizar_window, text="ID do Agendamento:").pack()
    agendamento_id_entry = tk.Entry(atualizar_window)
    agendamento_id_entry.pack()

    tk.Label(atualizar_window, text="Novo Status:").pack()
    status_var = tk.StringVar()
    status_combobox = ttk.Combobox(atualizar_window, textvariable=status_var, state="readonly")
    status_combobox['values'] = ("pendente", "concluido", "cancelado")
    status_combobox.pack()

    def confirmar_atualizacao():
        agendamento_id = agendamento_id_entry.get()
        novo_status = status_var.get()

        if not agendamento_id or not novo_status:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos!")
            return

        sucesso = atualizar_status_agendamento(int(agendamento_id), novo_status)
        if sucesso:
            messagebox.showinfo("Sucesso", "Status atualizado!")
            atualizar_window.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao atualizar status. Verifique o ID.")

    tk.Button(atualizar_window, text="Confirmar Atualização", command=confirmar_atualizacao).pack(pady=10)
    
def abrir_cadastro_barbeiro():
    janela = tk.Toplevel()
    janela.title("Cadastro de Barbeiro")

    tk.Label(janela, text="Nome do Barbeiro:").pack(pady=5)
    entrada_nome = tk.Entry(janela)
    entrada_nome.pack(pady=5)

    def salvar():
        nome = entrada_nome.get()
        if nome.strip():
            cadastrar_barbeiro(nome.strip())
            messagebox.showinfo("Sucesso", "Barbeiro cadastrado com sucesso!")
            janela.destroy()
        else:
            messagebox.showwarning("Aviso", "Por favor, insira o nome.")

    tk.Button(janela, text="Cadastrar", command=salvar).pack(pady=10)

def exportar_agendamentos_excel():
    agendamentos = listar_agendamentos()

    if not agendamentos:
        messagebox.showinfo("Informação", "Nenhum agendamento encontrado para exportar.")
        return

    colunas = ["ID", "Cliente", "Serviço", "Data e Hora", "Status"]
    
    df = pd.DataFrame(agendamentos, columns=colunas)

    
    caminho_arquivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Arquivo Excel", "*.xlsx")])

    if caminho_arquivo:
        try:
            df.to_excel(caminho_arquivo, index=False)
            messagebox.showinfo("Sucesso", f"Agendamentos exportados para:\n{caminho_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {str(e)}")

def main():
    criar_tabelas()

    root = tk.Tk()
    root.title("Barber House")
    root.geometry("500x600")  
    root.configure(bg="#f0f0f0")  

    titulo = tk.Label(root, text="Barber House", font=("Arial", 24, "bold"), bg="#f0f0f0", fg="#333")
    titulo.pack(pady=20)

    botao_frame = tk.Frame(root, bg="#ffffff", bd=2, relief="groove")
    botao_frame.pack(padx=20, pady=10, fill="both", expand=True)

    botoes = [
        ("Cadastrar Cliente", cadastrar_cliente_janela),
        ("Cadastrar Serviço", cadastrar_servico_janela),
        ("Cadastrar Barbeiro", abrir_cadastro_barbeiro),
        ("Agendar Horário", agendar_horario_janela),
        ("Listar Agendamentos", listar_agendamentos_janela),
        ("Atualizar Status", atualizar_status_janela),
        ("Exportação de Dados", exportar_agendamentos_excel),
        ("Geração de Relatório", abrir_janela_relatorios)
    ]

    for texto, comando in botoes:
        btn = tk.Button(botao_frame, text=texto, width=30, height=2,
                        command=comando, bg="#007ACC", fg="white",
                        font=("Arial", 10, "bold"), relief="raised", bd=3, cursor="hand2")
        btn.pack(pady=8)

    root.mainloop()

def salvar_df_excel(df):
    caminho_arquivo = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Arquivo Excel", "*.xlsx")],
        title="Salvar Relatório"
    )

    if not caminho_arquivo:
        return

    try:
        df.to_excel(caminho_arquivo, index=False)
        messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso para:\n{caminho_arquivo}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar o relatório:\n{str(e)}")
        
def salvar_df_com_grafico(df, titulo, x_col, y_col, cor='skyblue'):
    caminho_arquivo = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Arquivo Excel", "*.xlsx")],
        title="Salvar Relatório"
    )

    if not caminho_arquivo:
        return

    try:
        df.to_excel(caminho_arquivo, index=False)

        df.plot(kind='bar', x=x_col, y=y_col, legend=False, color=cor)
        plt.title(titulo)
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.tight_layout()
        plt.show()

        messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso para:\n{caminho_arquivo}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar o relatório:\n{str(e)}")


def gerar_relatorio_detalhado_agendamentos():
    df = gerar_dados_relatorio_detalhado()
    if df.empty:
        messagebox.showinfo("Informação", "Nenhum agendamento encontrado.")
        return
    salvar_df_excel(df)


def gerar_relatorio_por_servico():
    df = gerar_dados_relatorio_por_servico()
    if df.empty:
        messagebox.showinfo("Informação", "Nenhum dado encontrado.")
        return

    pivot = df.pivot(index='Serviço', columns='Status', values='Quantidade').fillna(0)
    pivot.plot(kind='bar', stacked=True, color=["lightgreen", "tomato", "gray"])
    plt.title("Agendamentos por Serviço e Status")
    plt.xlabel("Serviço")
    plt.ylabel("Quantidade")
    plt.tight_layout()
    plt.show()

    caminho_arquivo = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Arquivo Excel", "*.xlsx")],
        title="Salvar Relatório por Serviço"
    )

    if caminho_arquivo:
        try:
            df.to_excel(caminho_arquivo, index=False)
            messagebox.showinfo("Sucesso", f"Relatório exportado para:\n{caminho_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{str(e)}")


def gerar_relatorio_por_barbeiro():
    df = gerar_dados_relatorio_por_barbeiro()
    if df.empty:
        messagebox.showinfo("Informação", "Nenhum dado encontrado.")
        return
    salvar_df_com_grafico(df, "Atendimentos por Barbeiro", "Barbeiro", "Total de Atendimentos Realizados", cor="goldenrod")


def gerar_relatorio_mensal_recebimentos():
    df = gerar_dados_relatorio_mensal_recebimentos()
    if df.empty:
        messagebox.showinfo("Informação", "Nenhum dado encontrado.")
        return
    salvar_df_com_grafico(df, "Recebimentos Mensais", "Mês", "Total Recebido", cor="mediumseagreen")

def abrir_janela_relatorios():
    relatorio_window = tk.Toplevel()
    relatorio_window.title("Relatórios")
    relatorio_window.geometry("400x300")

    ttk.Label(relatorio_window, text="Escolha o tipo de relatório:", font=("Arial", 12)).pack(pady=10)

    ttk.Button(relatorio_window, text="Relatório Detalhado de Agendamentos",
               command=gerar_relatorio_detalhado_agendamentos).pack(pady=5)

    ttk.Button(relatorio_window, text="Relatório por Serviço (por Status)",
               command=gerar_relatorio_por_servico).pack(pady=5)

    ttk.Button(relatorio_window, text="Relatório por Barbeiro (quantos atendeu)",
               command=gerar_relatorio_por_barbeiro).pack(pady=5)

    ttk.Button(relatorio_window, text="Relatório Mensal de Recebimentos",
               command=gerar_relatorio_mensal_recebimentos).pack(pady=5)

if __name__ == "__main__":
    main()
    