<?php
declare(strict_types=1);

/**
 * Task Manager (taskmanager.codigo.co) HTTP client.
 *
 * Uses the stored better-auth session cookie so reporting does not ask for an
 * OTP on every export. Session material lives outside the web root in
 * /opt/taskmanager-session.
 */

class TaskManagerAuthException extends RuntimeException {}
class TaskManagerHttpException extends RuntimeException
{
    public int $statusCode;

    public function __construct(string $message, int $statusCode = 0)
    {
        parent::__construct($message);
        $this->statusCode = $statusCode;
    }
}

function tm_config(): array
{
    static $config = null;
    if (is_array($config)) {
        return $config;
    }

    $dir = '/opt/taskmanager-session';
    $env = tm_env_read($dir . '/.env');
    $config = [
        'dir' => $dir,
        'env_file' => $dir . '/.env',
        'session_file' => $dir . '/session.json',
        'people_file' => $dir . '/people.json',
        'status_file' => $dir . '/status.json',
        'base_url' => rtrim((string)($env['TM_BASE_URL'] ?? 'https://taskmanager.codigo.co'), '/'),
        'email' => (string)($env['TM_EMAIL'] ?? ''),
        'password' => (string)($env['TM_PASSWORD'] ?? ''),
        'project_id' => (string)($env['TM_PROJECT_ID'] ?? ''),
        'project_name' => (string)($env['TM_PROJECT_NAME'] ?? ''),
    ];

    return $config;
}

function tm_env_read(string $path): array
{
    if (!is_file($path) || !is_readable($path)) {
        return [];
    }

    $env = [];
    $lines = file($path, FILE_IGNORE_NEW_LINES);
    if (!is_array($lines)) {
        return [];
    }
    foreach ($lines as $raw) {
        $line = trim((string)$raw);
        if ($line === '' || str_starts_with($line, '#') || strpos($line, '=') === false) {
            continue;
        }
        [$key, $value] = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value);
        if ($key === '') {
            continue;
        }
        $len = strlen($value);
        if ($len >= 2) {
            $first = $value[0];
            $last = $value[$len - 1];
            if (($first === '"' && $last === '"') || ($first === "'" && $last === "'")) {
                $value = substr($value, 1, -1);
            }
        }
        $env[$key] = $value;
    }

    return $env;
}

function tm_project_id(): string
{
    return trim((string)(tm_config()['project_id'] ?? ''));
}

function tm_project_name(): string
{
    return trim((string)(tm_config()['project_name'] ?? ''));
}

function tm_user_agent(): string
{
    return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36';
}

function tm_json_read_file(string $path): array
{
    if (!is_file($path)) {
        return [];
    }
    $decoded = json_decode((string)file_get_contents($path), true);
    return is_array($decoded) ? $decoded : [];
}

function tm_json_write_file(string $path, array $data): void
{
    $json = json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    if ($json === false) {
        throw new RuntimeException('Unable to encode Task Manager state.');
    }
    if (@file_put_contents($path, $json . "\n", LOCK_EX) === false) {
        throw new RuntimeException('Unable to write Task Manager state at ' . $path . '.');
    }
}

function tm_session_read(): array
{
    $session = tm_json_read_file((string)tm_config()['session_file']);
    if (!isset($session['cookies']) || !is_array($session['cookies'])) {
        $session['cookies'] = [];
    }
    return $session;
}

function tm_session_write(array $session): void
{
    $session['saved_at'] = gmdate('c');
    tm_json_write_file((string)tm_config()['session_file'], $session);
}

function tm_session_cookie_header(array $session): string
{
    $now = time();
    $parts = [];
    foreach (($session['cookies'] ?? []) as $cookie) {
        if (!is_array($cookie)) {
            continue;
        }
        $name = trim((string)($cookie['name'] ?? ''));
        if ($name === '') {
            continue;
        }
        $expires = (int)($cookie['expires'] ?? 0);
        if ($expires > 0 && $expires < $now) {
            continue;
        }
        $parts[] = $name . '=' . (string)($cookie['value'] ?? '');
    }
    return implode('; ', $parts);
}

function tm_header_values(array $headers, string $name): array
{
    $needle = strtolower($name) . ':';
    $out = [];
    foreach ($headers as $line) {
        if (str_starts_with(strtolower((string)$line), $needle)) {
            $out[] = trim(substr((string)$line, strlen($needle)));
        }
    }
    return $out;
}

function tm_header_value(array $headers, string $name): string
{
    $values = tm_header_values($headers, $name);
    return $values ? (string)$values[0] : '';
}

function tm_parse_set_cookie(string $line, string $baseUrl): ?array
{
    $parts = explode(';', $line);
    $first = array_shift($parts);
    if (!is_string($first) || strpos($first, '=') === false) {
        return null;
    }
    [$name, $value] = explode('=', $first, 2);
    $name = trim($name);
    if ($name === '') {
        return null;
    }

    $host = (string)(parse_url($baseUrl, PHP_URL_HOST) ?: '');
    $cookie = [
        'name' => $name,
        'value' => trim($value),
        'domain' => $host,
        'path' => '/',
        'expires' => 0,
        'secure' => false,
        'httpOnly' => false,
    ];

    foreach ($parts as $part) {
        $part = trim((string)$part);
        if ($part === '') {
            continue;
        }
        $kv = explode('=', $part, 2);
        $key = strtolower(trim($kv[0]));
        $val = isset($kv[1]) ? trim($kv[1]) : '';
        if ($key === 'domain') {
            $cookie['domain'] = ltrim($val, '.');
        } elseif ($key === 'path') {
            $cookie['path'] = $val !== '' ? $val : '/';
        } elseif ($key === 'expires') {
            $ts = strtotime($val);
            if ($ts !== false) {
                $cookie['expires'] = $ts;
            }
        } elseif ($key === 'max-age') {
            $cookie['expires'] = time() + (int)$val;
        } elseif ($key === 'secure') {
            $cookie['secure'] = true;
        } elseif ($key === 'httponly') {
            $cookie['httpOnly'] = true;
        }
    }

    return $cookie;
}

function tm_cookies_from_headers(array $headers, string $baseUrl): array
{
    $cookies = [];
    foreach (tm_header_values($headers, 'set-cookie') as $line) {
        $cookie = tm_parse_set_cookie($line, $baseUrl);
        if ($cookie !== null) {
            $cookies[] = $cookie;
        }
    }
    return $cookies;
}

function tm_cookie_key(array $cookie): string
{
    return strtolower((string)($cookie['name'] ?? '')) . '|' . strtolower((string)($cookie['domain'] ?? '')) . '|' . (string)($cookie['path'] ?? '/');
}

function tm_session_merge_cookies(array $session, array $newCookies): array
{
    $map = [];
    foreach (($session['cookies'] ?? []) as $cookie) {
        if (is_array($cookie)) {
            $map[tm_cookie_key($cookie)] = $cookie;
        }
    }
    foreach ($newCookies as $cookie) {
        if (is_array($cookie)) {
            $map[tm_cookie_key($cookie)] = $cookie;
        }
    }
    $now = time();
    $cookies = [];
    foreach ($map as $cookie) {
        $expires = (int)($cookie['expires'] ?? 0);
        if ($expires > 0 && $expires < $now) {
            continue;
        }
        $cookies[] = $cookie;
    }
    $session['cookies'] = array_values($cookies);
    return $session;
}

function tm_http_request(
    string $method,
    string $path,
    ?string $body = null,
    array $extraHeaders = [],
    ?array $cookieList = null,
    bool $persistCookies = true,
    bool $throwOnAuth = true
): array {
    $config = tm_config();
    $url = $config['base_url'] . $path;
    $session = $cookieList === null ? tm_session_read() : ['cookies' => $cookieList];
    $useStoredSession = $cookieList === null;

    $baseHeaders = [
        'Accept: application/json, text/csv, */*',
        'Accept-Language: en-SG,en;q=0.9',
        'User-Agent: ' . tm_user_agent(),
        'Referer: ' . $config['base_url'] . '/',
        'X-Requested-With: XMLHttpRequest',
    ];
    if (strtoupper($method) !== 'GET' && strtoupper($method) !== 'HEAD') {
        $baseHeaders[] = 'Origin: ' . $config['base_url'];
        $baseHeaders[] = 'Content-Type: application/json';
    }

    $maxAttempts = 5;
    for ($attempt = 0; $attempt < $maxAttempts; $attempt++) {
        $headers = $baseHeaders;
        $cookieHeader = tm_session_cookie_header($session);
        if ($cookieHeader !== '') {
            $headers[] = 'Cookie: ' . $cookieHeader;
        }
        foreach ($extraHeaders as $extra) {
            $headers[] = (string)$extra;
        }
        $headers = array_values(array_unique($headers));

        $responseHeaders = [];
        $ch = curl_init($url);
        if ($ch === false) {
            throw new TaskManagerHttpException('Unable to initialise Task Manager HTTP client.');
        }
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HEADER => false,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_TIMEOUT => 120,
            CURLOPT_CONNECTTIMEOUT => 20,
            CURLOPT_ENCODING => '',
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_SSL_VERIFYHOST => 2,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_CUSTOMREQUEST => strtoupper($method),
            CURLOPT_HEADERFUNCTION => static function ($handle, string $line) use (&$responseHeaders): int {
                $trimmed = trim($line);
                if ($trimmed !== '') {
                    $responseHeaders[] = $trimmed;
                }
                return strlen($line);
            },
        ]);
        if ($body !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        }

        $responseBody = curl_exec($ch);
        $curlErrorNo = curl_errno($ch);
        $curlError = curl_error($ch);
        $statusCode = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        curl_close($ch);

        if ($curlErrorNo !== 0) {
            if ($attempt < $maxAttempts - 1) {
                sleep(1 << $attempt);
                continue;
            }
            throw new TaskManagerHttpException('Task Manager connection failed: ' . $curlError);
        }

        $setCookies = tm_cookies_from_headers($responseHeaders, $config['base_url']);
        if ($persistCookies && $useStoredSession && $setCookies) {
            $session = tm_session_merge_cookies($session, $setCookies);
            tm_session_write($session);
        }

        if ($statusCode === 429) {
            $retryAfter = (int)tm_header_value($responseHeaders, 'retry-after');
            sleep($retryAfter > 0 ? min($retryAfter, 30) : 5);
            continue;
        }
        if ($statusCode >= 500 && $attempt < $maxAttempts - 1) {
            sleep(1 << $attempt);
            continue;
        }

        if ($statusCode === 401) {
            if (!$throwOnAuth) {
                return ['status' => $statusCode, 'headers' => $responseHeaders, 'body' => (string)$responseBody];
            }
            tm_status_write(['state' => 'expired', 'error' => 'HTTP 401', 'expires_at' => (string)($session['expires_at'] ?? '')]);
            throw new TaskManagerAuthException('Task Manager session expired. Reconnect at /reporting/connect.');
        }
        if ($statusCode === 403) {
            if (!$throwOnAuth) {
                return ['status' => $statusCode, 'headers' => $responseHeaders, 'body' => (string)$responseBody];
            }
            $lower = strtolower((string)$responseBody);
            if (strpos($lower, 'just a moment') !== false || strpos($lower, 'cloudflare') !== false) {
                throw new TaskManagerHttpException('Task Manager blocked the request (Cloudflare challenge).', 403);
            }
            tm_status_write(['state' => 'expired', 'error' => 'HTTP 403', 'expires_at' => (string)($session['expires_at'] ?? '')]);
            throw new TaskManagerAuthException('Task Manager denied access (403). Reconnect at /reporting/connect.');
        }
        if (in_array($statusCode, [301, 302, 303, 307, 308], true)) {
            $location = tm_header_value($responseHeaders, 'location');
            if ($location !== '' && strpos($location, 'sign-in') !== false) {
                tm_status_write(['state' => 'expired', 'error' => 'Redirected to sign-in', 'expires_at' => (string)($session['expires_at'] ?? '')]);
                throw new TaskManagerAuthException('Task Manager session expired. Reconnect at /reporting/connect.');
            }
        }

        return [
            'status' => $statusCode,
            'headers' => $responseHeaders,
            'body' => (string)$responseBody,
        ];
    }

    throw new TaskManagerHttpException('Task Manager request failed after retries.');
}

function tm_api_json(string $method, string $path, ?array $payload = null, ?array $cookieList = null): array
{
    $body = $payload === null ? null : json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    $response = tm_http_request($method, $path, $body, [], $cookieList);
    $status = (int)($response['status'] ?? 0);
    $decoded = json_decode((string)($response['body'] ?? ''), true);
    if ($status < 200 || $status >= 300) {
        $snippet = trim((string)($response['body'] ?? ''));
        if (strlen($snippet) > 300) {
            $snippet = substr($snippet, 0, 300);
        }
        throw new TaskManagerHttpException('Task Manager API ' . $status . ($snippet !== '' ? ': ' . $snippet : ''), $status);
    }
    if (!is_array($decoded)) {
        throw new TaskManagerHttpException('Task Manager returned malformed JSON.', $status);
    }
    return $decoded;
}

function tm_get_json(string $path): array
{
    return tm_api_json('GET', $path);
}

function tm_get_csv(string $path): string
{
    $response = tm_http_request('GET', $path);
    $status = (int)($response['status'] ?? 0);
    if ($status < 200 || $status >= 300) {
        throw new TaskManagerHttpException('Task Manager CSV export failed with status ' . $status, $status);
    }
    return (string)($response['body'] ?? '');
}

function tm_status_write(array $status): void
{
    $config = tm_config();
    $status['checked_at'] = gmdate('c');
    try {
        tm_json_write_file((string)$config['status_file'], $status);
    } catch (Throwable $e) {
        // Status reporting must never break the export.
    }
}

function tm_session_expiry(): string
{
    $session = tm_session_read();
    return trim((string)($session['expires_at'] ?? ''));
}

function tm_validate_session(): array
{
    $session = tm_session_read();
    $cookies = is_array($session['cookies'] ?? null) ? $session['cookies'] : [];
    if (!$cookies) {
        tm_status_write(['state' => 'expired', 'error' => 'No stored session', 'expires_at' => '']);
        throw new TaskManagerAuthException('No Task Manager session is stored. Connect at /reporting/connect.');
    }

    $data = tm_get_json('/api/auth/get-session');
    $sessionData = is_array($data['session'] ?? null) ? $data['session'] : [];
    $expiresAt = trim((string)($sessionData['expiresAt'] ?? ''));
    if (!empty($data['needsRefresh']) || !empty($sessionData['needsRefresh'])) {
        try {
            $refreshed = tm_api_json('POST', '/api/auth/get-session', []);
            if (is_array($refreshed['session'] ?? null)) {
                $sessionData = $refreshed['session'];
                $expiresAt = trim((string)($sessionData['expiresAt'] ?? $expiresAt));
            }
        } catch (Throwable $e) {
            // Keep the existing session if refresh fails.
        }
    }

    $session = tm_session_read();
    if ($expiresAt !== '') {
        $session['expires_at'] = $expiresAt;
    }
    if (!empty($data['user']['email'])) {
        $session['user_email'] = (string)$data['user']['email'];
    }
    tm_session_write($session);
    tm_status_write(['state' => 'ok', 'error' => '', 'expires_at' => (string)($session['expires_at'] ?? '')]);

    return $session;
}

function tm_keepalive(): array
{
    $session = tm_validate_session();
    return [
        'state' => 'ok',
        'expires_at' => (string)($session['expires_at'] ?? ''),
        'user_email' => (string)($session['user_email'] ?? ''),
    ];
}

function tm_people_map(?array $csvRows = null): array
{
    $map = tm_json_read_file((string)tm_config()['people_file']);
    $clean = [];
    foreach ($map as $name => $email) {
        $name = trim((string)$name);
        $email = trim((string)$email);
        if ($name !== '' && $email !== '') {
            $clean[$name] = $email;
        }
    }
    if (is_array($csvRows)) {
        foreach ($csvRows as $row) {
            if (!is_array($row)) {
                continue;
            }
            $name = trim((string)($row['Assignee'] ?? ''));
            $email = trim((string)($row['Assignee Email'] ?? ''));
            if ($name !== '' && $email !== '' && !isset($clean[$name])) {
                $clean[$name] = $email;
            }
        }
    }
    return $clean;
}
