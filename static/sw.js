// Version à incrémenter à chaque déploiement pour forcer la mise à jour sur mobile
const CACHE_VERSION = 'financewatch-v5';
const ASSETS = ['/', '/static/manifest.json'];

// Installation : mise en cache des assets de base
self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE_VERSION)
            .then(c => c.addAll(ASSETS))
            .then(() => self.skipWaiting()) // Activation immédiate sans attendre fermeture des onglets
    );
});

// Activation : supprime TOUS les vieux caches automatiquement
self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE_VERSION)
                    .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim()) // Prend le contrôle immédiatement sur tous les onglets ouverts
    );
});

// Push : affiche une notification quand une alerte prix se déclenche
self.addEventListener('push', e => {
    let data = { title: 'FinanceWatch AI', body: 'Nouvelle alerte prix !', symbol: '' };
    try { data = e.data.json(); } catch(err) {}
    e.waitUntil(
        self.registration.showNotification(data.title || 'FinanceWatch AI', {
            body: data.body || data.message || 'Nouvelle alerte !',
            icon: '/static/icon-192.png',
            badge: '/static/icon-192.png',
            tag: 'fw-alert-' + (data.symbol || Date.now()),
            renotify: true,
            vibrate: [200, 100, 200],
            data: { url: '/' }
        })
    );
});

// Clic sur notification : ouvre l'app
self.addEventListener('notificationclick', e => {
    e.notification.close();
    e.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
            for (const c of list) {
                if (c.url.includes(self.registration.scope) && 'focus' in c) return c.focus();
            }
            if (clients.openWindow) return clients.openWindow('/');
        })
    );
});

// Fetch : network-first pour le HTML (toujours la version fraîche), cache-fallback pour le reste
self.addEventListener('fetch', e => {
    // Les appels API ne passent jamais par le cache
    if (e.request.url.includes('/api/')) return;

    // Network-first : essaie le réseau, fallback sur le cache si hors-ligne
    e.respondWith(
        fetch(e.request)
            .then(response => {
                // Met à jour le cache avec la réponse fraîche
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_VERSION).then(c => c.put(e.request, clone));
                }
                return response;
            })
            .catch(() => caches.match(e.request))
    );
});
