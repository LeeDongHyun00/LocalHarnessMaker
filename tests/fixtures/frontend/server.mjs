import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
const page = readFileSync('index.html', 'utf8').replace('__FAULT__', JSON.stringify(process.env.FIXTURE_FAULT || ''));
createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'});
  res.end(page);
}).listen(Number(process.env.PORT || 3000), '0.0.0.0');
