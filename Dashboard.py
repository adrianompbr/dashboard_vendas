#%%
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout= 'wide')

def formata_numero (valor, prefixo = ''):
    for unidade in ['','mil']:
        if valor<1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhoes'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'

#Sidebar
regioes = ['Brasil','Centro-Oeste','Nordeste','Norte','Sudeste','Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o periodo', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)
query_string = {'regiao':regiao.lower(),'ano':ano}
#
response = requests.get(url, params= query_string)

dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format= '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]
#depurar
#st.write("Região selecionada:", regiao)
#st.write("Query enviada:", query_string)
#st.write("Status da resposta:", response.status_code)
#st.write("Conteúdo bruto da resposta:", response.text[:200])  # Só os 200 primeiros caracteres


# Tabelas

#Tabelas de receita
receitaUF = dados.groupby('Local da compra')[['Preço']].sum()
receitaUF = dados.drop_duplicates(subset='Local da compra')[['Local da compra','lat','lon']].merge(receitaUF, left_on='Local da compra',right_index = True).sort_values('Preço', ascending=False)
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = "M"))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
receita_categorias = dados.groupby('Categoria do Produto')['Preço'].sum().sort_values(ascending =False)
# Tabelas de quantidade
qntdUF = (
    dados['Local da compra']
    .value_counts()
    .reset_index(name='Quantidade')
    .rename(columns={'index': 'Local da compra'})
    .merge(
        dados.drop_duplicates(subset='Local da compra')[['Local da compra','lat','lon']],
        on='Local da compra'
    )
    .sort_values('Quantidade', ascending=False)
)


vendas_UF = pd.DataFrame(dados.groupby('Local da compra')['Preço']
                         .count())
vendas_UF = (
    dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']]
    .merge(vendas_UF, left_on = 'Local da compra', right_index = True)
    .sort_values('Preço', ascending = False)
    .rename(columns={'Preço': 'Quantidade'})
    )

vendas_mensal = (
    dados.set_index('Data da Compra')
    .groupby(pd.Grouper(freq = "M"))['Preço']
    .count().reset_index()
    .rename(columns={'Preço': 'Quantidade'}))
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mês'] = vendas_mensal['Data da Compra'].dt.month_name()

qntd_categorias = dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending=False)
qntd_categorias.name = 'Vendas'

#Tabelas vendedores

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum','count']))#Com o egg da pra calcular soma+couunt

#Graficos
fig_mapa_receita = px.scatter_geo(receitaUF,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size= 'Preço',
                                  template='seaborn',
                                  hover_name= 'Local da compra',
                                  hover_data= {'lat': False, 'lon': False},
                                  title= 'Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y = (0, receita_mensal['Preço'].max()),
                             color = 'Ano',
                             line_dash='Ano',
                             title = 'Receita Mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receitaUF.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top estados(receita)')
# Graficos quantidade de vendas
fig_vendas_estados = px.bar(vendas_UF.head(),
                             x = 'Local da compra',
                             y = 'Quantidade',
                             text_auto = True,
                             title = 'Top estados por vendas')

fig_vendas_mensal = px.line(vendas_mensal,
                             x = 'Mês',
                             y = 'Quantidade',
                             markers = True,
                             range_y = (0, vendas_mensal['Quantidade'].max()),
                             color = 'Ano',
                             line_dash='Ano',
                             title = 'Vendas Mensais')
fig_vendas_mensal.update_layout(yaxis_title = 'Quantidade')

fig_mapa_quantidade = px.scatter_geo(qntdUF,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size= 'Quantidade',
                                  template='seaborn',
                                  hover_name= 'Local da compra',
                                  hover_data= {'lat': False, 'lon': False},
                                  title= 'Quantidade por Estado')

fig_qntd_categorias = px.bar(qntd_categorias,
                                text_auto = True,
                                title = 'Quantidade por categoria')
#
fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto = True,
                                title = 'Receita por categoria')

fig_receita_categorias.update_layout(yaxis_title = 'Receita')
# Visualização
tab1,tab2,tab3 = st.tabs(["Receita","Quantidade de Vendas","Vendedores"])
with tab1:
    col1,col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(),'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width= True)
        st.plotly_chart(fig_receita_estados, use_container_width= True)
    with col2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width= True)
        st.plotly_chart(fig_receita_categorias, use_container_width= True)

with tab2:
    col1,col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(),'R$'))
        st.plotly_chart(fig_mapa_quantidade, use_container_width= True)
        st.plotly_chart(fig_vendas_estados, use_container_width= True) #

    with col2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width= True)
        st.plotly_chart(fig_qntd_categorias, use_container_width= True)

with tab3:
    qntd_vendedores = st.number_input('Quantidade Vendedores',2,20,4)
    col1,col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(),'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qntd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qntd_vendedores).index,
                                        text_auto= True,
                                        title= f'Top{qntd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)
    with col2:
        st.metric("Quantidade de vendas", formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qntd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qntd_vendedores).index,
                                        text_auto= True,
                                        title= f'Top{qntd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores)
#fromdict tranforma um json em dataframe
#response.json tranforma a requisição em json 
#%%