<?php
declare(strict_types=1);

/**
 * Task Manager authentication helpers.
 *
 * The normal path reuses /opt/taskmanager-session/session.json. When the session
 * expires, /reporting/connect drives the email-OTP flow without exposing the
 * stored password to the browser.
 */

function tm_h(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function tm_auth_error_message(array $response): string
{
    $body = (string)($response['body'] ?? '');
    $decoded = json_decode($body, true);
    if (is_array($decoded)) {
        $message = trim((string)($decoded['message'] ?? ''));
        if ($message !== '') {
            return $message;
        }
        $code = trim((string)($decoded['code'] ?? ''));
        if ($code !== '') {
            return $code;
        }
    }
    $snippet = trim($body);
    if ($snippet !== '') {
        return substr($snippet, 0, 200);
    }
    return 'Task Manager authentication failed.';
}

function tm_auth_start(): array
{
    $config = tm_config();
    if ($config['email'] === '' || $config['password'] === '') {
        throw new RuntimeException('Task Manager credentials are not configured.');
    }

    $payload = json_encode([
        'email' => $config['email'],
        'password' => $config['password'],
    ], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

    $response = tm_http_request('POST', '/api/auth/sign-in/email', (string)$payload, [], [], false, false);
    $cookies = tm_cookies_from_headers((array)($response['headers'] ?? []), $config['base_url']);
    $status = (int)($response['status'] ?? 0);
    if ($status < 200 || $status >= 300) {
        throw new RuntimeException(tm_auth_error_message($response));
    }

    $decoded = json_decode((string)($response['body'] ?? ''), true);
    $twoFactor = is_array($decoded) && !empty($decoded['twoFactorRedirect']);
    if ($twoFactor) {
        $message = 'A 6-digit code was sent to ' . $config['email'] . '.';
        try {
            $resend = tm_auth_resend($cookies);
            $cookies = is_array($resend['cookies'] ?? null) ? $resend['cookies'] : $cookies;
            $message = 'A new sign-in code was sent to ' . $config['email'] . '.';
        } catch (Throwable $e) {
            $message = 'Sign-in needs a code, but the send request failed: ' . $e->getMessage();
        }
        return [
            'two_factor' => true,
            'cookies' => $cookies,
            'session' => null,
            'message' => $message,
        ];
    }

    $session = tm_auth_save_session($cookies);
    return [
        'two_factor' => false,
        'cookies' => $cookies,
        'session' => $session,
        'message' => 'Task Manager connected.',
    ];
}

function tm_auth_resend(array $cookies): array
{
    $response = tm_http_request('POST', '/api/auth/two-factor/send-otp', '{}', [], $cookies, false, false);
    $status = (int)($response['status'] ?? 0);
    if ($status < 200 || $status >= 300) {
        throw new RuntimeException(tm_auth_error_message($response));
    }
    $newCookies = tm_cookies_from_headers((array)($response['headers'] ?? []), tm_config()['base_url']);
    return ['cookies' => tm_session_merge_cookies(['cookies' => $cookies], $newCookies)['cookies']];
}

function tm_auth_verify(string $code, array $cookies): array
{
    $code = trim($code);
    if (!preg_match('/^\d{4,8}$/', $code)) {
        throw new RuntimeException('Enter the 6-digit code from the email.');
    }

    $payload = json_encode(['code' => $code], JSON_UNESCAPED_SLASHES);
    $response = tm_http_request('POST', '/api/auth/two-factor/verify-otp', (string)$payload, [], $cookies, false, false);
    $status = (int)($response['status'] ?? 0);
    $newCookies = tm_cookies_from_headers((array)($response['headers'] ?? []), tm_config()['base_url']);
    $merged = tm_session_merge_cookies(['cookies' => $cookies], $newCookies)['cookies'];

    if ($status < 200 || $status >= 300) {
        throw new RuntimeException(tm_auth_error_message($response));
    }

    $session = tm_auth_save_session($merged);
    return ['cookies' => $merged, 'session' => $session];
}

function tm_auth_save_session(array $cookies): array
{
    $config = tm_config();
    $response = tm_http_request('GET', '/api/auth/get-session', null, [], $cookies, false, false);
    $status = (int)($response['status'] ?? 0);
    if ($status < 200 || $status >= 300) {
        throw new RuntimeException('Task Manager session could not be verified: ' . tm_auth_error_message($response));
    }

    $decoded = json_decode((string)($response['body'] ?? ''), true);
    if (!is_array($decoded) || !is_array($decoded['session'] ?? null)) {
        throw new RuntimeException('Task Manager returned an unexpected session response.');
    }

    $newCookies = tm_cookies_from_headers((array)($response['headers'] ?? []), $config['base_url']);
    $merged = tm_session_merge_cookies(['cookies' => $cookies], $newCookies)['cookies'];

    $sessionData = $decoded['session'];
    $session = [
        'base_url' => $config['base_url'],
        'saved_at' => gmdate('c'),
        'expires_at' => trim((string)($sessionData['expiresAt'] ?? '')),
        'user_email' => trim((string)($decoded['user']['email'] ?? $config['email'])),
        'cookies' => $merged,
    ];
    tm_session_write($session);
    tm_status_write(['state' => 'ok', 'error' => '', 'expires_at' => (string)$session['expires_at']]);
    return $session;
}

function tm_connect_csrf_token(): string
{
    if (empty($_SESSION['tm_connect_csrf'])) {
        $_SESSION['tm_connect_csrf'] = bin2hex(random_bytes(16));
    }
    return (string)$_SESSION['tm_connect_csrf'];
}

function tm_connect_csrf_check(): void
{
    $posted = (string)($_POST['csrf'] ?? '');
    $expected = (string)($_SESSION['tm_connect_csrf'] ?? '');
    if ($expected === '' || !hash_equals($expected, $posted)) {
        http_response_code(400);
        echo 'Invalid request token.';
        exit;
    }
}

function tm_connect_pending_cookies(): array
{
    $at = (int)($_SESSION['tm_pending_at'] ?? 0);
    if ($at <= 0 || (time() - $at) > 1800) {
        unset($_SESSION['tm_pending_cookies'], $_SESSION['tm_pending_at']);
        return [];
    }
    $cookies = $_SESSION['tm_pending_cookies'] ?? [];
    return is_array($cookies) ? $cookies : [];
}

function tm_connect_set_pending(array $cookies): void
{
    $_SESSION['tm_pending_cookies'] = $cookies;
    $_SESSION['tm_pending_at'] = time();
}

function tm_connect_clear_pending(): void
{
    unset($_SESSION['tm_pending_cookies'], $_SESSION['tm_pending_at']);
}

function tm_connect_rate_limited(): bool
{
    $now = time();
    $attempts = $_SESSION['tm_connect_attempts'] ?? [];
    $attempts = is_array($attempts) ? $attempts : [];
    $attempts = array_values(array_filter($attempts, static fn($ts): bool => is_int($ts) && $ts >= ($now - 600)));
    $_SESSION['tm_connect_attempts'] = $attempts;
    return count($attempts) >= 5;
}

function tm_connect_record_attempt(): void
{
    $attempts = $_SESSION['tm_connect_attempts'] ?? [];
    $attempts = is_array($attempts) ? $attempts : [];
    $attempts[] = time();
    $_SESSION['tm_connect_attempts'] = $attempts;
}

function tm_connect_two_factor_expiry(): int
{
    foreach (tm_connect_pending_cookies() as $cookie) {
        if (is_array($cookie) && ($cookie['name'] ?? '') === '__Secure-better-auth.two_factor') {
            return (int)($cookie['expires'] ?? 0);
        }
    }
    return 0;
}

function tm_render_connect_page(string $error = '', string $notice = ''): void
{
    $session = tm_session_read();
    $expiresAt = trim((string)($session['expires_at'] ?? ''));
    $userEmail = trim((string)($session['user_email'] ?? ''));
    $pending = tm_connect_pending_cookies();
    $codeExpiry = tm_connect_two_factor_expiry();
    $csrf = tm_connect_csrf_token();

    echo '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>Connect Task Manager</title><style>';
    echo 'body{font-family:Georgia,"Times New Roman",serif;background:#f7f4ee;color:#1f1a12;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;padding:1.25rem;box-sizing:border-box;}';
    echo '.card{width:min(520px,100%);background:#fffdf8;border:1px solid #ddd2bf;border-radius:10px;padding:1.1rem 1.2rem;box-shadow:0 10px 30px rgba(31,26,18,.08);}';
    echo 'h1{margin:0 0 .4rem;font-size:1.3rem;} .muted{color:#6d5f4e;font-size:.95rem;}';
    echo 'label{display:block;margin:.8rem 0 .35rem;font-size:.92rem;} input{width:100%;box-sizing:border-box;border:1px solid #d8c9b2;border-radius:7px;padding:.55rem .65rem;}';
    echo 'button{margin-top:1rem;border:1px solid #c8b79f;background:#7d2b1f;color:#fff;padding:.55rem .9rem;border-radius:7px;cursor:pointer;} button:hover{background:#652116;}';
    echo 'a{color:#7d2b1f;} .error{border:1px solid #e2b8b0;background:#fff2f0;color:#8c261a;border-radius:7px;padding:.55rem .65rem;margin:.4rem 0 .7rem;}';
    echo '.ok{border:1px solid #b9d7b0;background:#f2fbf0;color:#265d1c;border-radius:7px;padding:.55rem .65rem;margin:.4rem 0 .7rem;}';
    echo 'code{background:#f1ece2;padding:.1rem .3rem;border-radius:4px;}';
    echo '</style></head><body><div class="card">';
    echo '<h1>Connect Task Manager</h1>';
    echo '<p class="muted">' . ($userEmail !== '' ? 'Signed in as <strong>' . tm_h($userEmail) . '</strong>.' : 'No Task Manager session is stored.') . '</p>';
    if ($expiresAt !== '') {
        echo '<p class="muted">Session expires: <strong>' . tm_h($expiresAt) . '</strong></p>';
    }
    if ($error !== '') {
        echo '<div class="error">' . tm_h($error) . '</div>';
    }
    if ($notice !== '') {
        echo '<div class="ok">' . tm_h($notice) . '</div>';
    }

    if ($pending) {
        if ($codeExpiry > 0) {
            $left = $codeExpiry - time();
            if ($left > 0) {
                $expiryLabel = (new DateTimeImmutable('@' . $codeExpiry))->setTimezone(new DateTimeZone('Asia/Singapore'))->format('H:i:s');
                echo '<p class="muted">Code window: enter it by <strong>' . tm_h($expiryLabel) . ' SGT</strong> (about ' . (int)ceil($left / 60) . ' min left).</p>';
            } else {
                echo '<div class="error">The code window has expired. Click "Send a new code" to restart sign-in and get a fresh code.</div>';
            }
        }
        echo '<form method="post" action="/reporting/connect/verify" autocomplete="off">';
        echo '<input type="hidden" name="csrf" value="' . tm_h($csrf) . '">';
        echo '<label for="code">6-digit code from the email</label>';
        echo '<input id="code" name="code" type="text" inputmode="numeric" pattern="[0-9]{4,8}" maxlength="8" required autofocus>';
        echo '<button type="submit">Verify and connect</button></form>';
        echo '<form method="post" action="/reporting/connect/resend" style="display:inline-block;margin-right:.6rem;">';
        echo '<input type="hidden" name="csrf" value="' . tm_h($csrf) . '">';
        echo '<button type="submit" style="background:#fff;color:#7d2b1f;">Send a new code</button></form>';
        echo '<form method="post" action="/reporting/connect/cancel" style="display:inline-block;">';
        echo '<input type="hidden" name="csrf" value="' . tm_h($csrf) . '">';
        echo '<button type="submit" style="background:#fff;color:#7d2b1f;">Cancel</button></form>';
        echo '<p class="muted" style="margin-top:.8rem;">Email delivery can be slow. Use the newest email and enter it before the deadline shown above. If it arrives late, click "Send a new code" to restart the window.</p>';
    } else {
        echo '<form method="post" action="/reporting/connect/start">';
        echo '<input type="hidden" name="csrf" value="' . tm_h($csrf) . '">';
        echo '<button type="submit">Send a login code</button></form>';
        echo '<p class="muted" style="margin-top:.8rem;">The password is read from the server config; you only enter the emailed code.</p>';
    }

    echo '<p style="margin-top:1rem;"><a href="/reporting">&larr; Back to reporting</a></p>';
    echo '</div></body></html>';
}
