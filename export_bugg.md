Problem: `export` funkar inte för stora resurser som `npegl_eng`. Det tar för lång
tid att extrahera datan, så anslutningen får timeout innan backenden är klar.

Därför finns en annan metod - `export2` - på v5 på k2, där vi testat att
använda kod från Korp som hanterar detta genom att skicka blanksteg var 15e sekund.

Koden finns längst ner i `src/server/searching.py`.
Vi använder dekoratorerna `@main_handler` och `@prevent_timeout` från Korp (något
förenklade). I nuvarande version skickas datan i chunks, vars storlek sätts i
url:en: `https://ws.spraakbanken.gu.se/karp/v5/export2/chunk_size`

Att skicka datan i chunks eller i helhet verkar inte ha någon inverkan på resultatet.

När man kör backenden lokalt (`python run.py 5002`) har inga fel uppstått under
den lilla testning som gjorts,
men när man kör backenden med `supervisord` så går det sönder ca 1/3 av gångerna.

Resultatet blir då att data börjar skickas (ett antal mellanslag), men sedan
stängs överföringen:
```sh
> curl 'https://ws.spraakbanken.gu.se/ws/karp/v5/export2/npegl_eng/5000' -i -u '...'
  HTTP/1.1 200 OK
  Date: Wed, 20 Jun 2018 09:22:38 GMT
  Server: Apache/2.4.18 (Fedora)
  Content-Type: application/json
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: HEAD, OPTIONS, GET
  Access-Control-Max-Age: 21600
  Access-Control-Allow-Headers: CONTENT-TYPE, AUTHORIZATION
  Via: 1.1 ws.spraakbanken.gu.se
  Transfer-Encoding: chunked

  {
  ...

  curl: (18) transfer closed with outstanding read data remaining
`
