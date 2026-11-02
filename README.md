# Samsung TV Tizen — Free My TV Variant

Variante independente do [Free My TV](https://github.com/simbasjungles/free-my-tv),
baseada no commit `a9e1027`, para a Samsung UN65DU8000GXZD com Tizen 9.0.
HTML, CSS e JavaScript originais, com preparação local em Python (biblioteca padrão).
Não é um produto oficial Samsung nem uma instalação validada da variante na DU8000.

## Estrutura

```text
web/                    Interface original, ícones, fontes, traduções e moedas
tizen/                  Manifesto e ícone da variante
scripts/                Preparação Web e utilitários de geração
docs/                   Documentação, origem e inventário da migração
tests/                  Validações locais sem SDK e sem rede
dist/preview/           Prévia gerada para navegador (ignorada)
dist/tizen/             Projeto gerado para o SDK (ignorado)
backups/                Cópias locais da aplicação e saídas anteriores (ignoradas)
```

Edite os fontes, não `dist/`. Não abra a raiz do repositório como projeto de
empacotamento: ela contém documentação, scripts e backups que não pertencem ao WGT.

Novos subdiretórios em `web/` precisam ser registrados em `scripts/webapp.py`:
o gerador não copia diretórios arbitrários recursivamente. Depois, regenere ambas
as saídas e execute os testes de recursos.

## Prévia no Chrome

Execute na raiz do repositório:

```powershell
python -B scripts/prepare_preview.py
python -m http.server 8765 --bind 127.0.0.1 --directory dist/preview
```

Abra http://127.0.0.1:8765 e use setas, Enter e Escape/Backspace.
Use viewport 1920×1080 para comparar o palco original; a escala e o alinhamento
seguem o upstream. Encerre o servidor com Ctrl+C.
Não abra `web/index.html` diretamente: `config.js`, `coins.js` e `i18n.js` são gerados.

No navegador, apps e entradas são demonstrativos. Sem chave TMDb, os pôsteres
podem não aparecer. Clima, cotações e recomendações dependem de serviços externos;
as preferências e chaves inseridas na interface ficam no armazenamento do navegador/TV.
Os geradores usam padrões genéricos: não leem `config.properties` ou certificados,
não acessam a rede e não executam build, assinatura ou instalação.

## Preparar os recursos Tizen

```powershell
python -B scripts/prepare_tizen.py
```

Isso escreve apenas `dist/tizen/`, incluindo o manifesto, os recursos e
`tizen_web_project.yaml` com uma lista explícita. Não produz `.wgt`.
Para um build futuro autorizado, abra **somente `dist/tizen/`** em outra janela
do VS Code e selecione essa pasta como projeto ativo. A configuração local
`.vscode/settings.json` da raiz não foi alterada e pode ainda apontar para a raiz.

- Package ID: `FmtvDU8a01`.
- Application ID: `FmtvDU8a01.FreeMyTVVariant`.
- Nome de saída: `FreeMyTVVariant`; versão: `0.1.0`; API mínima: `2.3`.
- `signing_profile: ""`: mantém o perfil ativo do SDK; não cria nem altera certificados.

Não utilizar os fluxos Android, TizenBrew ou instalação do README upstream para
esta preparação. O adaptador e a navegação originais foram preservados, inclusive
o retorno Samsung por `hide()`. A variante ainda requer validação na televisão.

## Validar

Após preparar ambas as saídas:

```powershell
python -B -m unittest discover -s tests -v
```

Os testes permanentes comparam as saídas com os fontes atuais e validam recursos,
licenças, identidade e lista de empacotamento. Permitem personalizações legítimas
sem exigir igualdade com o upstream. Não executam SDK, rede ou instalação.

A auditoria histórica é separada e opcional:

```powershell
python -B tests/audit_migration.py
```

Ela verifica o inventário da importação `a9e1027` (exceto os arquivos adaptados
na migração) e o backup local, quando disponível. Mudanças visuais futuras podem
produzir diferenças esperadas nessa auditoria; não atualize o inventário histórico
para ocultá-las. Ela não faz parte do comando de testes permanentes acima.

## Origem e preservação

Os commits `954fbb4` (Home anterior) e `3042272` (importação da variante)
permanecem no histórico. A aplicação anterior também está em
`backups/previous-app/`; as saídas antigas estão em `backups/migration-workspace/`.
Esses backups são locais: não acompanham um clone. Consulte
[a migração](docs/MIGRATION.md) e o [inventário](docs/migration-inventory.json).

Licença [MIT](LICENSE), preservando o copyright do Free My TV.
Veja [créditos de terceiros](THIRD_PARTY_NOTICES.md) e o
[README upstream integral](docs/UPSTREAM_README.md). O documento upstream é histórico:
seus caminhos e instruções de instalação referem-se ao repositório original.
