<?php
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}

require __DIR__ . '/taskmanager_client.php';

try {
    $result = tm_keepalive();
    echo json_encode($result, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . "\n";
    exit(0);
} catch (TaskManagerAuthException $e) {
    tm_status_write([
        'state' => 'expired',
        'error' => $e->getMessage(),
        'expires_at' => tm_session_expiry(),
    ]);
    fwrite(STDERR, 'EXPIRED: ' . $e->getMessage() . "\n");
    exit(2);
} catch (Throwable $e) {
    tm_status_write([
        'state' => 'error',
        'error' => $e->getMessage(),
        'expires_at' => tm_session_expiry(),
    ]);
    fwrite(STDERR, 'ERROR: ' . $e->getMessage() . "\n");
    exit(1);
}
