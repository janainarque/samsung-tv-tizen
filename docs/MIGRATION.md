# Migração para a estrutura principal

Base importada: `simbasjungles/free-my-tv`, revisão `a9e1027`.
Branch de trabalho: `migration/free-my-tv-base`.
Antes da reorganização, Git limpo e commits `954fbb4` e `3042272` confirmados.

## Mapeamento

| Origem | Destino |
| --- | --- |
| `migration/free-my-tv/web/` | `web/` |
| `migration/free-my-tv/app/assets/fonts/` | `web/fonts/` |
| `migration/free-my-tv/app/assets/symbols/` | `web/symbols/` |
| `migration/free-my-tv/app/assets/i18n/` | `web/i18n/` |
| `migration/free-my-tv/app/res/drawable/coin_*.xml` | `web/coins/` |
| `migration/free-my-tv/tools/*.py` | `scripts/` |
| `migration/free-my-tv/prepare_*.py` | `scripts/` |
| `migration/free-my-tv/tizen/` | `tizen/` |
| `migration/free-my-tv/LICENSE` | `LICENSE` |
| README e README upstream da variante | `docs/MIGRATION_PREPARATION.md`, `docs/UPSTREAM_README.md` |
| Aplicação anterior da raiz | `backups/previous-app/` |
| Diretórios antigos gerados e resíduos da migração | `backups/migration-workspace/` |

O inventário JSON registra o SHA-256 de cada fonte antes da movimentação.
HTML, CSS, JavaScript, ícones, fonte, catálogos e moedas foram preservados byte a byte.
Os quatro scripts Python receberam ajustes de caminhos; a leitura de JavaScript
no utilitário de tradução também passou a fechar os arquivos explicitamente.
O manifesto recebeu apenas
uma correção no caminho documental do comentário XML. Seus IDs e privilégios não mudaram.
As saídas em `dist/` incluem os créditos e as licenças necessárias.

Movimentações físicas não reescrevem commits. Sem staging, o Git mostra remoções nos
caminhos antigos e arquivos novos nos destinos; a detecção de renomeações poderá
associá-los pelo conteúdo numa revisão/commit futuro. Nenhum commit foi criado aqui.

## Aplicação anterior

`backups/previous-app/` contém index.html, css/, js/, config.xml, YAML do SDK,
README e um inventário de hashes. A cópia foi verificada antes de continuar.
O commit `954fbb4` também permite recuperar os fontes anteriores independentemente
do backup local. A importação original está em `3042272`.
Não foram apagados os antigos pacotes em `Debug/`, `.tizen-rds/` ou `.vscode/`.
Nenhum arquivo em `C:\dev\free-my-tv` foi lido ou modificado nesta reorganização.

## Regeneração e limites

Os comandos `scripts/prepare_preview.py` e `scripts/prepare_tizen.py` só geram
recursos locais com configuração genérica; não usam as rotinas de build upstream.
`scripts/translate.py` conserva o utilitário original, com os caminhos ajustados;
seus modos de tradução remota não fazem parte da preparação e não foram executados.
`docs/MIGRATION_PREPARATION.md` conserva a documentação da etapa anterior, com
caminhos históricos, e não substitui o README atual.

Os testes são locais. Build/assinatura, análise do WGT, comportamento real da API,
retorno Samsung, desempenho e instalação na DU8000 permanecem para outra etapa.
Feche janelas do SDK que usem a pasta antiga antes de trabalhar com `dist/tizen`.
O diretório vazio `migration/free-my-tv/tizen-app/` permaneceu bloqueado por outro
processo durante a reorganização. Não contém arquivos; suas saídas anteriores
estão preservadas em `backups/migration-workspace/free-my-tv/tizen-app/`.
Pode ser removido depois de fechar o processo que o mantém aberto.
