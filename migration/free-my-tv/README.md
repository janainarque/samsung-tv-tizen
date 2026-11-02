# Prévia independente do Free My TV

Interface original de https://github.com/simbasjungles/free-my-tv,
importada do commit `a9e1027`. Consulte `UPSTREAM_README.md` para os créditos
originais e `LICENSE` para a licença MIT, incluindo o copyright dos colaboradores.
Os arquivos importados foram mantidos sem alterações.

Esta variante contém uma prévia no navegador e um projeto SDK Tizen isolado.
Não contém certificados nem scripts de instalação.
A aplicação funcional na raiz do projeto e seu pacote em Debug permanecem intactos.

## Abrir no Chrome

Na pasta `C:\dev\samsung-tv-tizen\migration\free-my-tv`:

```powershell
python prepare_preview.py
python -m http.server 8765 --bind 127.0.0.1 --directory preview
```

Abra http://127.0.0.1:8765 no Chrome. Use as setas, Enter e Escape/Backspace.
O mouse também permite explorar a interface original. Encerre o servidor com Ctrl+C.
Os arquivos da prévia já estão preparados; o primeiro comando só é necessário
para regenerá-los após alterações nos fontes.

## O que está preservado

- `web/`: HTML, CSS, navegação, configurações, integração de dados e adaptador de TV.
- `app/assets/`: traduções, símbolos e fonte Inter com suas licenças.
- `app/res/drawable/coin_*.xml`: os quatro recursos de moedas usados pelo gerador.
- `tools/webapp.py` e `tools/translate.py`: geradores originais usados localmente.
- `preview/`: interface pronta, incluindo `config.js`, `coins.js` e `i18n.js` gerados.

O script local chama apenas a geração de arquivos Web com os padrões genéricos
originais. Não chama os construtores Android/Tizen nem a rotina original de
prévia que remove o diretório de saída. Não lê chaves ou configurações pessoais.

## Limitações da prévia

No navegador, o adaptador original oferece aplicativos e entradas demonstrativos:
não descobre nem abre os aplicativos da televisão. Não há uma chave TMDb embutida;
as recomendações e imagens dependem de uma chave configurada na própria interface.
O visual inicial pode, portanto, mostrar o relógio sem os pôsteres de filmes.
Clima e cotações dependem da internet, como no original. As preferências ficam no
armazenamento local do navegador e podem ser diferentes das da televisão.

O retorno Samsung com `hide()` e o botão Home só poderão ser validados na TV.
O projeto SDK está preparado; build, assinatura e instalação ainda não foram executados.
Não executar os fluxos de instalação descritos no README original para esta prévia.

## Créditos e licenças

Preservados: MIT do Free My TV (`LICENSE`), Apache 2.0 dos Material Symbols
(`app/assets/symbols/LICENSE-material-symbols.txt`) e SIL OFL da Inter
(`app/assets/fonts/OFL.txt`). Esses recursos e suas licenças também estão na prévia.
Os créditos completos de TMDb, Open-Meteo, Binance, logos e demais contribuições
permanecem no `UPSTREAM_README.md`, inclusive dentro da prévia.

## Faixa clara à direita no Chrome

O palco original tem 1920×1080 e `fit()` usa a menor escala entre largura e altura
no navegador, alinhando o palco no canto superior esquerdo. Não há corte nem
deformação. Em uma janela mais larga que 16:9, sobra uma área com o fundo claro
original à direita. O Chrome headless mediu viewport 1898×982, palco
1745,78×982 e sobra de 152,22 px; em viewport 1578×902 a sobra à direita foi zero.
Isso reproduz o comportamento previsto pelo original, sem evidência de defeito
que justifique mudar o CSS. Para comparar com a TV, use uma área útil 1920×1080
na emulação de dispositivo do Chrome (a janela externa inclui barras e abas).
No Tizen, o original usa a largura da janela, inclusive quando o teclado abre.
Nenhum arquivo visual foi alterado.

## Projeto Samsung independente

- Manifesto fonte: `tizen/config.xml`.
- Ícone original: `tizen/icon.png`.
- Preparação local: `prepare_tizen.py` (somente escreve recursos e YAML).
- Raiz a abrir no SDK: `tizen-app/`.
- Manifesto efetivo: `tizen-app/config.xml`.
- Configuração do SDK: `tizen-app/tizen_web_project.yaml`.
- Nome: `Free My TV Variant`; versão local: `0.1.0`.
- Package ID: `FmtvDU8a01`.
- Application ID: `FmtvDU8a01.FreeMyTVVariant`.

Esses IDs diferem tanto da aplicação anterior quanto do Free My TV oficial.
O mínimo de API continua 2.3, como no original e no projeto funcional; Tizen 9.0
é o alvo de validação, sem introduzir chamadas exclusivas dessa versão.
O adaptador original descobre o próprio ID em execução para removê-lo da lista
de aplicativos; não precisa ser reescrito para esses identificadores.

O manifesto mantém as declarações Samsung do original: internet para dados e
imagens; rede pública para os fallbacks locais de abertura; application.launch
para abrir apps; tv.window para entradas de vídeo; tv.inputdevice é conservada
por paridade com o manifesto original, embora o código atual não registre teclas
adicionais. Não há privilégio novo em relação ao upstream. O acesso de rede
continua amplo (`origin="*"`), como no original; não foi alterada sua política.
Nenhum botão Home é registrado ou remapeado. Voltar continua usando `hide()`.

### Preparar e fazer build isolado no SDK existente

Os arquivos já estão preparados. Para regenerar após futuras mudanças:

```powershell
cd C:\dev\samsung-tv-tizen\migration\free-my-tv
python prepare_tizen.py
```

Esse comando não cria WGT e não usa a CLI ou o SDK. Não lê `config.properties`;
gera configurações genéricas sem chave TMDb. O YAML enumera todos os 79 recursos,
incluindo configurações geradas, traduções, fontes, ícones, manifesto e licenças.
Para mudar a identidade, edite o manifesto fonte e regenere, não a cópia de saída.

Quando for a etapa autorizada de build:

1. Abra **somente** `C:\dev\samsung-tv-tizen\migration\free-my-tv\tizen-app`
   em uma nova janela do VS Code com o SDK existente.
2. Selecione essa pasta como projeto Tizen ativo. Confira que o projeto ativo não
   aponta para `C:\dev\samsung-tv-tizen`; não use a configuração `.vscode` da raiz.
3. Confira `profile: tv-samsung`, `output_name: FreeMyTVVariant` e os IDs acima.
   `signing_profile: ""` mantém o esquema atual, que usa o perfil ativo existente;
   a configuração não cria, importa ou altera certificados. Confirme no SDK qual
   perfil está ativo antes de qualquer operação que assine.
4. Use a ação de **build** já utilizada no SDK. Não selecione Run, Debug ou Deploy.
   Se o SDK combinar build e assinatura, execute apenas quando ambas estiverem
   autorizadas. A saída padrão será dentro do projeto isolado, em `Debug/`.
5. Confira o manifesto e os recursos do pacote antes de uma instalação futura.
   Não atualize nem desinstale o aplicativo anterior.

O YAML segue o esquema do projeto funcional, mas sua aceitação e o nome final do
artefato ainda precisam ser confirmados por um build futuro. Não executar o
`build.sh` Android nem `tizen/build.py` do repositório original para esta variante.
Não há automatização de instalação ou de acesso à TV nesta preparação.
