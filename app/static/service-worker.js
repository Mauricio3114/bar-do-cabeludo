const CACHE_NAME = "bar-cabeludo-v1";

const ARQUIVOS_BASICOS = [
    "/static/manifest.json",
    "/static/icons/icon-192.png",
    "/static/icons/icon-512.png",
    "/static/icons/icon-maskable-512.png",
    "/static/img/logo-cabeludo.png"
];


self.addEventListener("install", event => {

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(ARQUIVOS_BASICOS);
            })
    );

    self.skipWaiting();

});


self.addEventListener("activate", event => {

    event.waitUntil(

        caches.keys().then(keys => {

            return Promise.all(

                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))

            );

        })

    );

    self.clients.claim();

});


self.addEventListener("fetch", event => {

    /*
     * O sistema depende do servidor para pedidos,
     * mesas, caixa etc.
     *
     * Por isso NÃO vamos cachear respostas dinâmicas.
     * O cache fica somente para os arquivos estáticos.
     */

    if (event.request.method !== "GET") {
        return;
    }

    const url = new URL(event.request.url);

    if (!url.pathname.startsWith("/static/")) {
        return;
    }

    event.respondWith(

        caches.match(event.request)
            .then(cached => {

                if (cached) {
                    return cached;
                }

                return fetch(event.request);

            })

    );

});