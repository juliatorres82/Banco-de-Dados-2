
# Documentação: 

## Dados escolhidos: Cadastro Único

### Inserção de novos dados sem duplicatas: 

Fizemos out join de todas as tabelas juntando-as através da DATA. Como as datas no Cadastro Único aparecem no formato mm/yyyy (e não dd/mm/yyyy), as colocamos como tipo TEXT (ou o postgres não aceitaria).

Para o tratamento de dados, usamos o pandas: criamos um dataframe com todas as linhas da coluna 'Data' existentes em todas as tables utilizadas e redefinimos esta coluna como unique(retiramos apenas os valores existentes uma única vez, sem duplicatas). POr fim, utilizamos este dataframe gerado para criar o join (merge) de dados entre todas as tabelas escolhidas.


### Tempo de execução da query:
O tempo de execução da consulta foi de 0.0555 segundos.