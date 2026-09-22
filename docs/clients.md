# MCP istemcilerine bağlanma

Kanonik remote endpoint:

```text
https://mevzuat.sorgunbogaz.com/mcp
```

Bu endpoint Streamable HTTP ve standart MCP araç keşfini kullanır. Core backend
OpenAI, Anthropic veya başka bir sağlayıcı SDK'sına bağlı değildir.

## MCP Inspector

```bash
npx @modelcontextprotocol/inspector https://mevzuat.sorgunbogaz.com/mcp
```

Inspector sürümünüz URL argümanını desteklemiyorsa UI açıldıktan sonra
Transport olarak Streamable HTTP, URL olarak yukarıdaki endpoint'i seçin.

## Claude Code

Proje `.mcp.json` dosyası:

```json
{
  "mcpServers": {
    "turkiye-health-tourism-regulations": {
      "type": "http",
      "url": "https://mevzuat.sorgunbogaz.com/mcp"
    }
  }
}
```

Claude Desktop veya Claude.ai arayüzündeki alan adları sürüme/üyeliğe göre
değişebilir. Remote MCP URL alanı sunuluyorsa aynı endpoint'i kullanın. Bu
projede canlı Claude hesabı testi yapılması gerekmez.

## Codex / diğer istemciler

Streamable HTTP MCP URL isteyen istemcilerde aynı endpoint'i kullanın. Stdio
gereken istemciler için repository'yi yerel kurup `dis-mevzuat serve` komutunu
çalıştırın.

## Bağımsız doğrulama

```bash
python scripts/mcp_smoke.py https://mevzuat.sorgunbogaz.com/mcp
```

Bu test sağlayıcı hesabı olmadan handshake, discovery, schema, annotations,
search ve fetch akışını doğrular.
