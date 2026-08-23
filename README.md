# Controle de Insumos

MVP em Django para cadastro de produtos e lojas, entradas, saídas, histórico,
pedidos, romaneios e administração.

## Instalação no Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Abra `http://127.0.0.1:8000/` no navegador. A administração fica em
`http://127.0.0.1:8000/admin/`.

Como alternativa, dê dois cliques em `INSTALAR_E_INICIAR.bat`. O arquivo cria
o ambiente virtual, instala o Django, prepara o banco e inicia o servidor.

## Importar a planilha de produtos

A planilha recebida está incluída em `dados/Pasta1.xlsx`. Depois da instalação,
dê dois cliques em `IMPORTAR_PRODUTOS.bat`. A importação:

- lê `TIPO`, `DESCRIÇÃO`, `TOTAL` e `OBS`;
- gera códigos a partir da linha de origem: `INS-0001`, `INS-0002` e assim por diante;
- em descrições repetidas, mantém somente a linha com maior `TOTAL`;
- em caso de empate, mantém a primeira ocorrência;
- registra o ajuste de saldo no histórico;
- pode ser executada novamente sem duplicar o estoque.

Também é possível enviar outra planilha pela página **Produtos**.

## Importar lojas

Na página **Lojas**, use o formulário **Importar cronograma** e selecione o PDF.
O sistema lê `CÓDIGO`, `NOME DA LOJA` e `LANE`, cria as novas lojas e atualiza
os códigos já cadastrados. Se uma loja aparecer em mais de uma lane, todas são
preservadas. Novas lojas também podem ser cadastradas manualmente.

## Solicitação digital de pedidos

O processo substitui a planilha pelo fluxo abaixo:

1. A loja entra com seu próprio usuário, seleciona produtos e quantidades e
   envia a solicitação.
2. O Supply Chain confere, ajusta, devolve para correção, recusa ou encaminha
   para aprovação.
3. O supervisor/gerente aprova, ajusta e aprova, devolve ou recusa.
4. A equipe de separação registra o atendimento total, parcial, falta de
   estoque ou devolução por divergência.
5. Ao concluir a separação, o estoque é baixado e o pedido entra no romaneio
   consolidado da loja. Cada loja possui um único romaneio, que reúne todos os
   seus pedidos separados. Esse é o fim do fluxo.

A loja visualiza somente seus próprios pedidos. Supply Chain, aprovadores e
separação visualizam a fila geral, mas cada perfil recebe somente os botões
correspondentes à sua etapa. Ajustes, devoluções, recusas e cancelamentos exigem
justificativa.

### Criar usuários e atribuir perfis

Depois de executar as migrações, entre em `/admin/`, abra **Usuários** e crie
os acessos. No mesmo cadastro, preencha o **Perfil de acesso**:

- **Loja:** selecione obrigatoriamente a loja vinculada;
- **Supply Chain:** confere e encaminha solicitações;
- **Supervisor/Gerente aprovador:** aprova pedidos de todas as lojas;
- **Equipe de separação:** registra quantidades separadas e divergências, baixa
  o estoque e gera o romaneio ao concluir;
- **Administrador:** possui acesso completo.

Usuários antigos sem perfil não acessam a operação. Superusuários e membros da
equipe do Django continuam sendo reconhecidos como administradores.

### Criar os acessos das lojas pela planilha FY27

Entre como administrador e abra **Importar logins** no menu. Envie a planilha
`Logins_Lojas_FY27.xlsx`. Para cada linha válida, o sistema:

- usa o código da loja como login;
- cria a loja se ela ainda não existir e atualiza seu nome;
- cria o usuário com o perfil **Loja** e o vincula à loja correta;
- armazena somente o hash da senha temporária;
- obriga o usuário a cadastrar uma nova senha no primeiro acesso.

Por segurança, usuários já existentes não têm sua senha modificada, a menos
que o administrador marque explicitamente a opção de redefinição. A planilha
de credenciais contém senhas temporárias e não deve ser enviada ao GitHub.

O pedido impresso em A4 paisagem mostra quantidades solicitadas, aprovadas e
separadas, além dos responsáveis e horários de cada etapa. Um pedido que já
teve o estoque baixado não pode ser excluído para preservar a auditoria.

## Fluxo inicial sugerido

1. Cadastre uma loja.
2. Cadastre um produto e informe o estoque mínimo.
3. Registre uma entrada.
4. Registre uma saída e, se necessário, vincule a uma loja.
5. Consulte o histórico e o dashboard.
6. Crie os usuários e atribua os perfis operacionais.
7. Faça uma solicitação com o usuário da loja e percorra as etapas até concluir
   a separação.

O banco local é o arquivo `db.sqlite3`. Faça cópias de segurança periódicas.

## Publicação: GitHub + Neon PostgreSQL + Render

O projeto usa SQLite no computador e muda automaticamente para PostgreSQL
quando a variável `DATABASE_URL` é configurada. O arquivo `db.sqlite3`, o
ambiente `.venv`, senhas e backups não são enviados ao GitHub.

### 1. Enviar o projeto ao GitHub

A opção mais simples no Windows é instalar o GitHub Desktop, escolher
**File > Add local repository**, selecionar esta pasta e clicar em
**Publish repository**. Marque **Keep this code private** se o sistema for de
uso interno da empresa.

Também é possível usar o PowerShell, depois de criar um repositório vazio no
GitHub:

```powershell
Set-Location "C:\CAMINHO\DA\PASTA\CONTROLE_INSUMOS"
Test-Path .\manage.py
git init
git add .
git commit -m "Preparar sistema para produção"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/controle-insumos.git
git push -u origin main
```

O comando `Test-Path` precisa retornar `True`. Se retornar `False`, abra no
PowerShell a pasta que realmente contém o arquivo `manage.py` antes de continuar.

### 2. Criar o banco no Neon

Crie um projeto separado chamado `controle-insumos`. No painel do Neon, abra
**Connect**, selecione a conexão **Pooled** e copie a URL completa. Ela começa
com `postgresql://` e termina normalmente com `sslmode=require`. Essa URL é uma
senha: não cole no código, no README nem no GitHub.

### 3. Publicar no Render

No painel do Render, escolha **New > Blueprint**, conecte o GitHub e selecione
o repositório. O arquivo `render.yaml` configura instalação, arquivos estáticos,
migrações e o servidor Gunicorn. Quando solicitado, informe em `DATABASE_URL`
a URL copiada do Neon e conclua a implantação.

O domínio público será parecido com
`https://controle-insumos.onrender.com`. O Render adiciona esse domínio
automaticamente aos hosts permitidos pelo Django.

### 4. Criar o primeiro administrador no Neon

Depois que a implantação terminar, abra **Shell** no serviço do Render e rode:

```bash
python manage.py createsuperuser
```

### 5. Copiar os dados atuais do SQLite para o Neon (opcional)

Primeiro, no PowerShell local, exporte os registros atuais:

```powershell
.\.venv\Scripts\python.exe manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude admin.logentry --indent 2 --output dados_backup.json
```

Em seguida, defina temporariamente a URL do Neon, aplique as migrações e
importe o arquivo:

```powershell
$env:DATABASE_URL="COLE_A_URL_DO_NEON_AQUI"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py loaddata dados_backup.json
Remove-Item Env:DATABASE_URL
```

O arquivo `dados_backup.json` fica ignorado pelo Git para não publicar dados da
empresa. Depois de conferir o sistema no Render, guarde o backup em local
seguro ou apague-o do computador.
