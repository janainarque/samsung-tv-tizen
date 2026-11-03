# Localização e disponibilidade de idiomas

Os destaques TMDB de filmes e séries usam `language=pt-BR` nas listas e no
catálogo de gêneros. O título localizado tem prioridade; se estiver vazio,
usa-se `original_title` ou `original_name`. Não é feita tradução automática.
Gêneros ausentes são omitidos. `overview` preserva a sinopse retornada na
consulta localizada; sem texto, fica vazio. O idioma efetivo de cada campo
não é certificado pelo parâmetro da consulta. A sinopse fica apenas nos dados
e no cache, sem adicionar conteúdo ou mudar a geometria do cartão.

O cache continua com validade de seis horas e fallback antigo em falhas.
Entradas antigas sem sinopse continuam válidas até a renovação normal.

No AniList, os títulos documentados são `english`, `romaji` e `native`.
Mantemos essa ordem de fallback, ignorando campos vazios. A descrição não
oferece argumento de idioma PT-BR. Sinônimos não possuem identificação de
idioma confiável para escolher uma tradução brasileira. Não traduzimos ou
relacionamos títulos com catálogos de streaming por semelhança de nomes.

## Áudio e legendas

Cada destaque normalizado possui `languageAvailability: []`. Vazio significa
**desconhecido**, não ausência de dublagem ou legendas. Tanto respostas da API
quanto cache são normalizados sem aceitar alegações de disponibilidade.
Não existe produtor confiável desses dados nesta integração; por isso nenhum
indicador “Dublado PT-BR” ou “Legendado PT-BR” é renderizado nesta etapa.
O cartão também não interpreta flags arbitrárias recebidas de outras fontes.

Uma futura entrada precisará conter, no mínimo: fonte oficial e URL de
evidência, identificador exato do título na plataforma, região `BR`, idioma
`pt-BR`, tipo de faixa (áudio ou legenda), escopo confirmado (título completo,
temporada ou episódio) e data de verificação. Dados restritos a um episódio
não poderão gerar um indicador de disponibilidade para a série inteira.
Esse é um contrato futuro, não um adaptador implementado ou uma autorização
para confiar em objetos preenchidos no cache.

TMDB Watch Providers indica provedores por país, não faixas de idioma.
`original_language`, `spoken_languages`, país, interface em português ou
presença no catálogo não comprovam dublagem nem legendas. A documentação
pública consultada do AniList não fornece essas faixas por plataforma/região.
Netflix e Crunchyroll orientam a consulta nos próprios títulos/players;
a disponibilidade pode variar por região, temporada, episódio e aparelho.
Não foi identificada uma API pública dessas plataformas utilizável neste
projeto, sem novas credenciais, que forneça essa confirmação. Não foram usados
scraping, APIs privadas nem correspondências entre IDs de fontes distintas.

Fontes oficiais consultadas:

- [TMDB: idiomas](https://developer.themoviedb.org/docs/languages)
- [TMDB: Watch Providers](https://developer.themoviedb.org/reference/movie-watch-providers)
- [AniList: MediaTitle](https://github.com/AniList/ApiV2-GraphQL-Docs/blob/master/docs/reference/object/mediatitle.md)
- [AniList: Media e descrição](https://github.com/AniList/ApiV2-GraphQL-Docs/blob/master/docs/reference/object/media.md)
- [Netflix: disponibilidade de idiomas e temporadas](https://help.netflix.com/pt/node/101798)
- [Crunchyroll: idiomas disponíveis](https://help.crunchyroll.com/pt-BR/article/What-languages-are-available-for-shows)
