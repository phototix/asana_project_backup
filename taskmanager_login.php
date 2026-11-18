<?php
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}

require __DIR__ . '/taskmanager_client.php';
require __DIR__ . '/taskmanager_auth.php';

try {
    echo "Starting Task Manager sign-in for " . tm_config()['email'] . "...\n";
    $start = tm_auth_start();
    if (!empty($start['two_factor'])) {
        echo (string)($start['message'] ?? 'A code was sent.') . "\n";
        echo 'Enter the 6-digit code: ';
        $code = trim((string)fgets(STDIN));
        $verified = tm_auth_verify($code, is_array($start['cookies'] ?? null) ? $start['cookies'] : []);
        $session = is_array($verified['session'] ?? null) ? $verified['session'] : [];
    } else {
        $session = is_array($start['session'] ?? null) ? $start['session'] : [];
    }

    echo "Connected.\n";
    echo 'Session expires: ' . (string)($session['expires_at'] ?? 'unknown') . "\n";
    exit(0);
} catch (Throwable $e) {
    fwrite(STDERR, 'ERROR: ' . $e->getMessage() . "\n");
    exit(1);
}
