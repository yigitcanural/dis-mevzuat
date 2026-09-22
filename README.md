# Türkiye Sağlık Turizmi Mevzuatı

Türkiye'deki sağlık turizmi, sağlık hizmetlerinde tanıtım, sosyal medya ve
mahremiyet kurallarını AI araçlarında **resmî kaynakları ve sürüm bilgisiyle**
araştırmaya yarayan provider-neutral bir MCP/RAG backend'i.

Mevcut diş hekimliği kaynaklarını korur; hastaneler, tıp merkezleri, diş
klinikleri, saç ekimi, estetik/plastik cerrahi, bariatrik cerrahi, göz,
aracı kuruluşlar ve hasta koordinasyonu gibi alanlara genişleyebilen bir
metadata ve retrieval yapısı sunar.

> Bu servis hukuki danışmanlık, yayın izni, tıbbi teşhis veya tedavi planı
> vermez. Güncel ve bağlayıcı metin için sonuçtaki resmî bağlantı kontrol edilir.

## Normal kullanıcı

**ChatGPT Plugin — review pending.** OpenAI Plugin Directory onayı tamamlanmadan
"ChatGPT'de Kullan" bağlantısı aktifmiş gibi sunulmaz.

Public sürüm yalnız kaynak arar ve getirir. Hasta verisi istemez; kaynak ekleme,
silme, arşivleme veya reindex aracı yayınlamaz.

## Claude ve diğer MCP istemcileri

Remote MCP istemcisinde şu URL kullanılır:

```text
https://mevzuat.sorgunbogaz.com/mcp
```

Claude hesabı bu projenin kurulumu veya testi için gerekli değildir. Aynı
endpoint FastMCP Client, MCP Inspector, Claude.ai, Claude Desktop, Claude Code
ve Streamable HTTP destekleyen diğer MCP istemcileriyle kullanılabilir.
Bağlantı örnekleri [docs/clients.md](docs/clients.md) içindedir.

## Developer: hızlı başlangıç

Python 3.11+:

```bash
git clone https://github.com/yigitcanural/dis-mevzuat.git
cd dis-mevzuat
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
dis-mevzuat status
dis-mevzuat serve
```

Yeni genel komut adı da aynıdır; eski komut geriye uyumluluk için korunur:

```bash
saglik-turizmi-mevzuat status
```

Hazır indeks, API anahtarı olmadan SQLite FTS5 ile çalışır.

## Docker

```bash
git clone https://github.com/yigitcanural/dis-mevzuat.git
cd dis-mevzuat
cp .env.example .env
docker compose up -d --build
curl http://127.0.0.1:8000/readyz
```

Container `restart: unless-stopped`, read-only root filesystem, düşürülmüş
Linux capability'leri, kalıcı `./data` mount'u, healthcheck ve dönen JSON
log limitleriyle gelir. Port yalnız `127.0.0.1` üzerinde yayınlanır.

## Mimari

```text
MCP client
  -> HTTPS / Cloudflare Tunnel
  -> public FastMCP (yalnız read-only araçlar)
  -> lexical FTS5
  -> optional semantic retrieval
  -> reciprocal-rank hybrid sıralama
  -> yalnız current kaynak filtresi
  -> data + meta + evidence

Resmî URL
  -> SSRF/domain/boyut kontrolü
  -> parse + normalize + SHA-256
  -> staging preview
  -> açık insan onayı
  -> chunk/index
  -> önceki sürümü archive
```

SQLite + FTS5 ana retrieval katmanıdır. Ağır bir vector database veya framework
eklenmemiştir. Embedding kapalıyken sistem tamamen işlevseldir.

## Public MCP araçları

- `search_regulations`: current kaynaklarda lexical/hybrid arama
- `list_sources`: kaynak kataloğu ve resmî kanıt künyeleri
- `get_source`: kaynak ve isteğe bağlı tüm parçaları
- `get_chunk`: tek madde/parça ve tam kanıt bilgisi
- `get_source_status`: sürüm, tarih ve current/archive durumu
- `system_status`: indeks ve retrieval sağlığı

Bütün public araçlar `readOnlyHint=true`, `destructiveHint=false`,
`idempotentHint=true`, `openWorldHint=false` bildirir.

`search_regulations` sonuçları üç ana bölüm taşır:

- `data`: kaynak metni ve ilgili madde/bölüm
- `meta`: kurum, kategori, tarih, sürüm, current/archive ve etiketler
- `evidence`: resmî URL, retrieval tarihi, statü ve SHA-256

0.x istemcileri kırmamak için eski üst seviye alanlar geçici olarak korunur.

## Admin ve public ayrımı

Public `serve` komutu hiçbir koşulda admin aracı kaydetmez. Kaynak yönetimi
ayrı process'tir:

```bash
dis-mevzuat serve-admin                    # stdio
dis-mevzuat serve-admin --transport http  # yalnız 127.0.0.1:8001
```

Admin akışı `preview -> insan onayı -> approve -> archive old version`
şeklindedir. `serve-admin` HTTP modunda loopback dışına bağlanmayı reddeder.

## Kaynaklar ve metadata

Hazır snapshot 15 kaynak ve 667 parça içerir. Kaynak önceliği:

1. Resmî Gazete
2. Sağlık Bakanlığı
3. KVKK
4. USHAŞ / HealthTürkiye
5. Diğer birincil ve resmî kurumlar

Desteklenen alanlar: başlık, kurum, resmî URL, yargı alanı, kategori,
alt kategori, kaynak türü, yayın/yürürlük/retrieval tarihleri, sürüm, durum,
SHA-256, etiketler ve current/archive.

Blog veya üçüncü taraf hukuk yorumu birincil mevzuat olarak eklenmemelidir.
Hazır snapshot'ın kesin kapsamı `data/seed_sources.json` içindedir.

## Semantik arama (isteğe bağlı)

```dotenv
DM_EMBEDDING_API_KEY=...
DM_EMBEDDING_API_BASE=https://openrouter.ai/api/v1
DM_EMBEDDING_MODEL=openai/text-embedding-3-small
```

Etkinleştirildiğinde sorgu embedding sağlayıcısına gider. Hasta veya klinik iç
verisi sorguya, indekse ya da embedding hizmetine gönderilmemelidir.

## Güvenlik

- Public MCP yalnız read-only ve no-auth'tur. Gerekçe: yalnız kamuya açık
  mevzuat okur, kullanıcı hesabı/verisi yoktur ve en geniş MCP istemci
  uyumluluğu hedeflenir.
- Abuse kontrolü: origin-side dakikalık limit, 1 MiB request sınırı, tool
  timeout, güvenlik başlıkları ve Cloudflare edge koruması.
- Uygulama erişim logları kapalıdır; ham IP saklanmaz. Hız limiti için süreç
  başına rastgele anahtarla türetilen geçici değer yaklaşık bir dakika tutulur.
- Kaynak alımı standart port, resmî domain allowlist'i, her redirect'te DNS/IP
  kontrolü ve maksimum byte sınırı uygular.
- Public process URL fetch veya database mutation aracı sunmaz.
- Origin portu public internete açılmaz; Cloudflare Tunnel kullanılır.

Ayrıntılı tehdit modeli: [docs/openai-submission/security-model.md](docs/openai-submission/security-model.md).

## Home Server ve remote MCP

Production, mevcut `home-server` Compose ağı ve `cloudflared` servisiyle
çalışacak şekilde tasarlanmıştır. Router port forwarding kullanılmaz.

- Local health: `http://127.0.0.1:8000/healthz`
- Local readiness: `http://127.0.0.1:8000/readyz`
- Public MCP: `https://mevzuat.sorgunbogaz.com/mcp`
- Landing: `https://mevzuat.sorgunbogaz.com/`

Deployment ve rollback adımları [docs/operations/home-server.md](docs/operations/home-server.md)
içindedir.

## Backup, restore ve update

```bash
./scripts/backup.sh
./scripts/restore.sh /path/to/backup-directory
./scripts/update.sh
```

Backup SQLite'ın online backup API'sini kullanır, raw resmî kaynakları ayrıca
paketler ve SHA-256 doğrulama listesi üretir. Backup'ı sunucudan bağımsız bir
konuma kopyalamak işletmecinin sorumluluğundadır. Update ve restore scriptleri,
`home-server-backend` ağı mevcutsa production Compose overlay'ini otomatik
kullanır.

## Kaynak güncelleme

```bash
DM_DATA_DIR=./data dis-mevzuat serve-admin
DM_DATA_DIR=./data dis-mevzuat seed data/seed_sources.json
```

`seed` de aynı preview/approval servis katmanını kullanır. Aynı hash ikinci kez
eklenmez; değişen sürüm açık onaydan sonra etkinleşir ve eski sürüm silinmeden
arşivlenir.

## Test ve bağımsız MCP doğrulaması

```bash
pip install -e ".[dev]"
pytest
python scripts/mcp_smoke.py http://127.0.0.1:8000/mcp
python scripts/mcp_smoke.py https://mevzuat.sorgunbogaz.com/mcp
```

Smoke aracı gerçek MCP handshake, tool discovery, annotations, search, fetch
ve admin izolasyonunu FastMCP'nin bağımsız client'ıyla doğrular.

## Sorun giderme

- `readyz` 503: `data/dis_mevzuat.sqlite3` mount'unu ve kaynak/parça sayısını kontrol edin.
- Boş arama: daha dar Türkçe anahtar kelime deneyin; bu, davranışın izinli olduğu anlamına gelmez.
- 429: bir dakika bekleyin veya kontrollü self-host kurulumunda limiti ayarlayın.
- Domain erişilemiyor: container health, `cloudflared` health ve Tunnel published-application route'unu kontrol edin.
- Embedding hatası: anahtarı kaldırarak lexical moda dönün; FTS5 bağımsız çalışır.

## OpenAI submission

Güncel Plugin Directory formu için kopyala-yapıştır paket ve test vakaları
[docs/openai-submission/README.md](docs/openai-submission/README.md) içindedir.
Eski 2023 `ai-plugin.json` manifesti kullanılmaz.

## Lisans ve kaynak metinleri

Kod MIT lisanslıdır. İndeksteki resmî metinler projeye ait değildir ve MIT
lisansı bu metinlere yeni bir lisans vermez. Her zaman resmî URL'deki güncel
metin esas alınır.
