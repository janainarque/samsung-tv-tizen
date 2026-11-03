# Cidade do clima

Sem cidade/coordenadas configuradas, o clima usa Brasília, DF, Brasil:
latitude `-15.7939`, longitude `-47.8828`. São coordenadas fixas da cidade,
não GPS ou localização precisa do usuário. A preferência manual salva tem
prioridade; configurações explícitas de cidade/coordenadas do build também
continuam respeitadas. A alteração do padrão não grava preferências.

Antes, o fallback vinha da cidade principal do fuso em `web/zones.js`:
`America/Sao_Paulo` apontava para São Paulo. Esse identificador de fuso também
é usado por Brasília, mas não determina o nome exibido. O relógio e a tabela
de fusos permanecem intactos. O Open-Meteo continua recebendo coordenadas e
`timezone=auto`, sem serviço adicional.

## Se o Chrome continuar mostrando São Paulo

O armazenamento pertence à origem e ao perfil: host, porta e perfil de uma
prévia temporária podem ser diferentes da aba que você utiliza normalmente.
Os testes isolados não permitem afirmar qual cidade está salva nessa aba.

Na aba da Home, o Console do DevTools permite consultar **somente a cidade**:

```javascript
JSON.parse(localStorage.getItem('fmtv.prefs') || '{}').city
```

`undefined` significa ausência dessa preferência; `"São Paulo"` significa
que a cidade está salva e deve continuar respeitada. Não imprima o objeto
completo de preferências: ele pode conter a chave TMDB.

Para escolher Brasília sem apagar outras configurações:

1. Abra **Settings → City** (Cidade).
2. Pesquise **Brasília**.
3. Confirme o resultado de **Distrito Federal, Brasil**.

O fluxo existente chama `Prefs.setCity()` para atualizar apenas cidade,
latitude e longitude; em seguida, `Data.cityChanged()` renova o clima.
A escolha persiste após recarregar. Não use `localStorage.clear()`, não remova
`fmtv.prefs` e não use a limpeza dos dados do site: isso pode apagar a chave
TMDB e outras preferências.
