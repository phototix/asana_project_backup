<?php
declare(strict_types=1);

session_start();

$webRoot = __DIR__;
$dataFile = $webRoot . '/data/backups.json';
$lastRunFile = $webRoot . '/data/last-run.json';
$envFile = $webRoot . '/.env';
$authAttemptsFile = $webRoot . '/data/auth-attempts.json';
$route = trim((string)($_GET['route'] ?? ''), '/');

function load_env_vars(string $path): array {
    if (!is_file($path)) {
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

function h(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function client_ip(): string {
    $remoteAddr = trim((string)($_SERVER['REMOTE_ADDR'] ?? ''));
    return $remoteAddr !== '' ? $remoteAddr : 'unknown';
}

function auth_attempts_read(string $path): array {
    $sessionAttempts = is_array($_SESSION['auth_attempts'] ?? null) ? $_SESSION['auth_attempts'] : [];
    if (!is_file($path)) {
        return $sessionAttempts;
    }
    $decoded = json_decode((string)file_get_contents($path), true);
    return is_array($decoded) ? $decoded : $sessionAttempts;
}

function auth_attempts_write(string $path, array $data): void {
    $_SESSION['auth_attempts'] = $data;
    $dir = dirname($path);
    if (!is_dir($dir)) {
        @mkdir($dir, 0775, true);
    }
    @file_put_contents($path, json_encode($data, JSON_UNESCAPED_SLASHES), LOCK_EX);
}

function auth_attempt_entry(array $allAttempts, string $ip, int $now, int $windowSeconds): array {
    $entry = is_array($allAttempts[$ip] ?? null) ? $allAttempts[$ip] : [];
    $failures = is_array($entry['failures'] ?? null) ? $entry['failures'] : [];
    $recentFailures = [];
    foreach ($failures as $ts) {
        $tsInt = (int)$ts;
        if ($tsInt > 0 && $tsInt >= ($now - $windowSeconds)) {
            $recentFailures[] = $tsInt;
        }
    }
    return [
        'failures' => $recentFailures,
        'locked_until' => max(0, (int)($entry['locked_until'] ?? 0)),
    ];
}

function auth_lockout_message(int $remainingSeconds): string {
    $remainingMinutes = (int)ceil($remainingSeconds / 60);
    if ($remainingMinutes <= 1) {
        return 'Too many failed attempts. Try again in about 1 minute.';
    }
    return 'Too many failed attempts. Try again in about ' . $remainingMinutes . ' minutes.';
}

function render_login_page(string $error = ''): void {
    http_response_code(200);
    $errorHtml = $error !== '' ? '<p class="error">' . h($error) . '</p>' : '';
    echo '<!doctype html>';
    echo '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>Login - Asana Backups</title>';
    echo '<style>';
    echo 'body{font-family:Georgia,"Times New Roman",serif;background:#f7f4ee;color:#1f1a12;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;padding:1.25rem;box-sizing:border-box;}';
    echo '.card{width:min(420px,100%);background:#fffdf8;border:1px solid #ddd2bf;border-radius:10px;padding:1.1rem 1.2rem;box-shadow:0 10px 30px rgba(31,26,18,.08);}';
    echo 'h1{margin:0 0 .4rem;font-size:1.35rem;}';
    echo '.muted{margin:0 0 1rem;color:#6d5f4e;font-size:.95rem;}';
    echo 'label{display:block;margin:.7rem 0 .35rem;font-size:.92rem;color:#3d301f;}';
    echo 'input{width:100%;box-sizing:border-box;border:1px solid #d8c9b2;border-radius:7px;padding:.55rem .65rem;background:#fff;color:#1f1a12;}';
    echo 'button{margin-top:1rem;border:1px solid #c8b79f;background:#7d2b1f;color:#fff;padding:.55rem .9rem;border-radius:7px;cursor:pointer;}';
    echo 'button:hover{background:#652116;}';
    echo '.error{border:1px solid #e2b8b0;background:#fff2f0;color:#8c261a;border-radius:7px;padding:.55rem .65rem;margin:.4rem 0 .7rem;}';
    echo '</style></head><body>';
    echo '<div class="card"><h1>Login Required</h1><p class="muted">Sign in to access backup files.</p>';
    echo $errorHtml;
    echo '<form method="post" action="/login" autocomplete="off">';
    echo '<label for="username">Username</label><input id="username" name="username" type="text" required autofocus>';
    echo '<label for="password">Password</label><input id="password" name="password" type="password" required>';
    echo '<button type="submit">Login</button></form></div></body></html>';
    exit;
}

function render_restricted_page(): void {
    http_response_code(403);
    echo '<!doctype html>';
    echo '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>Restricted - Asana Backups</title>';
    echo '<style>body{font-family:Georgia,"Times New Roman",serif;background:#f7f4ee;color:#1f1a12;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;padding:1.25rem;box-sizing:border-box;}';
    echo '.box{width:min(500px,100%);background:#fffdf8;border:1px solid #ddd2bf;border-radius:10px;padding:1.2rem;}';
    echo 'a{display:inline-block;margin-top:.7rem;color:#fff;background:#7d2b1f;border:1px solid #c8b79f;border-radius:7px;padding:.5rem .8rem;text-decoration:none;}a:hover{background:#652116;}</style>';
    echo '</head><body><div class="box"><h1>Restricted Page</h1><p>You must log in to access this page.</p><a href="/login">Go to login</a></div></body></html>';
    exit;
}

function json_read(string $path): array {
    if (!is_file($path)) {
        return [];
    }
    $decoded = json_decode((string)file_get_contents($path), true);
    return is_array($decoded) ? $decoded : [];
}

function format_bytes(int $bytes): string {
    if ($bytes < 1024) {
        return $bytes . ' B';
    }

    $units = ['KB', 'MB', 'GB', 'TB'];
    $size = (float)$bytes;
    $unit = 'B';
    foreach ($units as $next) {
        $size /= 1024;
        $unit = $next;
        if ($size < 1024) {
            break;
        }
    }

    return number_format($size, 2) . ' ' . $unit;
}

function format_datetime(string $value): string {
    if ($value === '') {
        return 'n/a';
    }

    try {
        $dt = new DateTimeImmutable($value);
        $sgt = $dt->setTimezone(new DateTimeZone('Asia/Singapore'));
        return $sgt->format('d M Y, h:i A') . ' SGT';
    } catch (Exception $e) {
        return $value;
    }
}

function format_run_stamp(string $value): string {
    if ($value === '') {
        return 'n/a';
    }

    if (preg_match('/^([0-9]{8})-([0-9]{6})$/', $value, $m)) {
        $dt = DateTimeImmutable::createFromFormat('YmdHis', $m[1] . $m[2], new DateTimeZone('UTC'));
        if ($dt instanceof DateTimeImmutable) {
            $sgt = $dt->setTimezone(new DateTimeZone('Asia/Singapore'));
            return $sgt->format('d M Y, h:i A') . ' SGT';
        }
    }

    return format_datetime($value);
}

function task_creator_label(array $task): string {
    $creator = is_array($task['created_by'] ?? null) ? $task['created_by'] : [];
    $name = trim((string)($creator['name'] ?? ''));
    $email = trim((string)($creator['email'] ?? ''));

    if ($name !== '') {
        return $name;
    }
    if ($email !== '') {
        return $email;
    }
    return 'n/a';
}

function task_group_label(array $task): string {
    $memberships = is_array($task['memberships'] ?? null) ? $task['memberships'] : [];
    $groups = [];
    foreach ($memberships as $membership) {
        if (!is_array($membership)) {
            continue;
        }
        $name = trim((string)($membership['section']['name'] ?? ''));
        if ($name !== '') {
            $groups[$name] = true;
        }
    }
    if (empty($groups)) {
        return 'Unsectioned';
    }
    return implode(' | ', array_keys($groups));
}

function local_asset_route(string $projectSlug, string $zipFile, string $assetType, string $taskGid, int $index): string {
    return '/view/' . rawurlencode($projectSlug)
        . '/' . rawurlencode($zipFile)
        . '/' . rawurlencode($assetType)
        . '/' . rawurlencode($taskGid)
        . '/' . rawurlencode((string)$index);
}

function rewrite_asana_asset_links(string $html, string $projectSlug, string $zipFile, string $taskGid, array $attachments): string {
    if ($html === '' || empty($attachments)) {
        return $html;
    }

    $attachmentIndexByGid = [];
    foreach ($attachments as $idx => $att) {
        if (!is_array($att)) {
            continue;
        }
        $gid = (string)($att['gid'] ?? '');
        if ($gid !== '') {
            $attachmentIndexByGid[$gid] = $idx + 1;
        }
    }

    if (empty($attachmentIndexByGid)) {
        return $html;
    }

    $html = preg_replace_callback('/<img\b[^>]*>/i', static function (array $m) use ($attachmentIndexByGid, $projectSlug, $zipFile, $taskGid): string {
        $tag = $m[0];
        if (!preg_match('/\bdata-asana-gid\s*=\s*"([0-9]+)"/i', $tag, $gidMatch)) {
            return $tag;
        }

        $gid = (string)$gidMatch[1];
        if (!isset($attachmentIndexByGid[$gid])) {
            return $tag;
        }

        $localUrl = local_asset_route($projectSlug, $zipFile, 'attachment', $taskGid, (int)$attachmentIndexByGid[$gid]);
        $updated = preg_replace('/\bsrc\s*=\s*(["\']).*?\1/i', 'src="' . $localUrl . '"', $tag, 1, $count);
        if ((int)$count === 0) {
            return $tag;
        }
        return (string)$updated;
    }, $html);

    $html = preg_replace_callback('/https:\/\/app\.asana\.com\/app\/asana\/-\/get_asset\?asset_id=([0-9]+)/i', static function (array $m) use ($attachmentIndexByGid, $projectSlug, $zipFile, $taskGid): string {
        $gid = (string)$m[1];
        if (!isset($attachmentIndexByGid[$gid])) {
            return $m[0];
        }
        return local_asset_route($projectSlug, $zipFile, 'attachment', $taskGid, (int)$attachmentIndexByGid[$gid]);
    }, $html);

    return $html;
}

function send_not_found(): void {
    http_response_code(404);
    echo 'Not found';
    exit;
}

function send_bad_request(string $message): void {
    http_response_code(400);
    echo $message;
    exit;
}

function find_project(array $projects, string $slug): ?array {
    foreach ($projects as $project) {
        if (($project['project_slug'] ?? '') === $slug) {
            return $project;
        }
    }
    return null;
}

function find_backup(array $project, string $zipFile): ?array {
    $backups = is_array($project['backups'] ?? null) ? $project['backups'] : [];
    foreach ($backups as $backup) {
        if (($backup['zip_file'] ?? '') === $zipFile) {
            return $backup;
        }
    }
    return null;
}

function open_zip(string $zipPath): ZipArchive {
    $zip = new ZipArchive();
    if ($zip->open($zipPath) !== true) {
        send_not_found();
    }
    return $zip;
}

function zip_json(ZipArchive $zip, string $entry): array {
    $data = $zip->getFromName($entry);
    if ($data === false) {
        return [];
    }
    $decoded = json_decode($data, true);
    return is_array($decoded) ? $decoded : [];
}

function list_zip_backup_data(string $zipPath): array {
    $zip = open_zip($zipPath);
    $tasks = [];
    $comments = [];
    $attachments = [];
    $inlineAssets = [];
    $boards = [];
    $sectionNames = [];
    $sectionOrder = [];
    $sections = zip_json($zip, 'sections.json');
    foreach ($sections as $section) {
        if (!is_array($section)) {
            continue;
        }
        $gid = (string)($section['gid'] ?? '');
        if ($gid === '') {
            continue;
        }
        $name = (string)($section['name'] ?? $gid);
        $sectionOrder[] = $gid;
        $sectionNames[$gid] = $name;
    }

    for ($i = 0; $i < $zip->numFiles; $i++) {
        $name = (string)$zip->getNameIndex($i);
        if (preg_match('#^tasks/([0-9]+)\.json$#', $name, $m)) {
            $task = zip_json($zip, $name);
            if (!empty($task)) {
                $taskGid = (string)$m[1];
                $tasks[$taskGid] = $task;
            }
            continue;
        }
        if (preg_match('#^comments/([0-9]+)\.json$#', $name, $m)) {
            $taskGid = (string)$m[1];
            $comments[$taskGid] = zip_json($zip, $name);
            continue;
        }
        if (preg_match('#^attachments/([0-9]+)/_meta\.json$#', $name, $m)) {
            $taskGid = (string)$m[1];
            $attachments[$taskGid] = zip_json($zip, $name);
            continue;
        }
        if (preg_match('#^inline-assets/([0-9]+)/_meta\.json$#', $name, $m)) {
            $taskGid = (string)$m[1];
            $inlineAssets[$taskGid] = zip_json($zip, $name);
            continue;
        }
    }

    foreach ($tasks as $taskGid => $task) {
        $memberships = is_array($task['memberships'] ?? null) ? $task['memberships'] : [];
        $assigned = false;
        foreach ($memberships as $membership) {
            $sectionGid = (string)($membership['section']['gid'] ?? '');
            $sectionName = (string)($membership['section']['name'] ?? '');
            if ($sectionGid === '') {
                $sectionGid = 'unsectioned';
            }
            if ($sectionName === '') {
                $sectionName = $sectionGid === 'unsectioned' ? 'Unsectioned' : $sectionGid;
            }
            $sectionNames[$sectionGid] = $sectionName;
            if (!isset($boards[$sectionGid])) {
                $boards[$sectionGid] = [];
            }
            $boards[$sectionGid][] = $taskGid;
            $assigned = true;
        }
        if (!$assigned) {
            if (!isset($sectionNames['unsectioned'])) {
                $sectionNames['unsectioned'] = 'Unsectioned';
            }
            if (!isset($boards['unsectioned'])) {
                $boards['unsectioned'] = [];
            }
            $boards['unsectioned'][] = $taskGid;
        }
    }

    $zip->close();

    foreach ($boards as $sectionGid => $taskIds) {
        usort($taskIds, static function (string $a, string $b) use ($tasks): int {
            $taskA = $tasks[$a] ?? [];
            $taskB = $tasks[$b] ?? [];
            $doneA = (bool)($taskA['completed'] ?? false);
            $doneB = (bool)($taskB['completed'] ?? false);
            if ($doneA !== $doneB) {
                return $doneA <=> $doneB;
            }
            return strnatcasecmp((string)($taskA['name'] ?? ''), (string)($taskB['name'] ?? ''));
        });
        $boards[$sectionGid] = $taskIds;
    }

    $orderedBoards = [];
    $used = [];
    foreach ($sectionOrder as $sectionGid) {
        if (!isset($boards[$sectionGid])) {
            continue;
        }
        $orderedBoards[] = [
            'gid' => $sectionGid,
            'name' => (string)($sectionNames[$sectionGid] ?? $sectionGid),
            'task_ids' => $boards[$sectionGid],
        ];
        $used[$sectionGid] = true;
    }

    $remaining = [];
    foreach ($boards as $sectionGid => $taskIds) {
        if (isset($used[$sectionGid]) || $sectionGid === 'unsectioned') {
            continue;
        }
        $remaining[] = [
            'gid' => $sectionGid,
            'name' => (string)($sectionNames[$sectionGid] ?? $sectionGid),
            'task_ids' => $taskIds,
        ];
    }
    usort($remaining, static function (array $a, array $b): int {
        return strnatcasecmp((string)($a['name'] ?? ''), (string)($b['name'] ?? ''));
    });
    foreach ($remaining as $board) {
        $orderedBoards[] = $board;
    }

    if (isset($boards['unsectioned'])) {
        $orderedBoards[] = [
            'gid' => 'unsectioned',
            'name' => (string)($sectionNames['unsectioned'] ?? 'Unsectioned'),
            'task_ids' => $boards['unsectioned'],
        ];
    }

    return [
        'tasks' => $tasks,
        'comments' => $comments,
        'attachments' => $attachments,
        'inline_assets' => $inlineAssets,
        'boards' => $orderedBoards,
    ];
}

function list_zip_status_counts(string $zipPath): array {
    $zip = open_zip($zipPath);
    $counts = [];

    $sections = zip_json($zip, 'sections.json');
    foreach ($sections as $section) {
        if (!is_array($section)) {
            continue;
        }
        $name = trim((string)($section['name'] ?? ''));
        if ($name === '') {
            continue;
        }
        if (!isset($counts[$name])) {
            $counts[$name] = 0;
        }
    }

    for ($i = 0; $i < $zip->numFiles; $i++) {
        $name = (string)$zip->getNameIndex($i);
        if (!preg_match('#^tasks/([0-9]+)\.json$#', $name)) {
            continue;
        }

        $task = zip_json($zip, $name);
        $memberships = is_array($task['memberships'] ?? null) ? $task['memberships'] : [];
        $taskStatuses = [];
        foreach ($memberships as $membership) {
            if (!is_array($membership)) {
                continue;
            }
            $statusName = trim((string)($membership['section']['name'] ?? ''));
            if ($statusName === '') {
                continue;
            }
            $taskStatuses[$statusName] = true;
        }

        if (empty($taskStatuses)) {
            if (!isset($counts['Unsectioned'])) {
                $counts['Unsectioned'] = 0;
            }
            $counts['Unsectioned'] += 1;
            continue;
        }

        foreach (array_keys($taskStatuses) as $statusName) {
            if (!isset($counts[$statusName])) {
                $counts[$statusName] = 0;
            }
            $counts[$statusName] += 1;
        }
    }

    $zip->close();
    return $counts;
}

function stream_zip_entry(string $zipPath, string $entryPath, bool $download = true): void {
    $zip = open_zip($zipPath);
    $stat = $zip->statName($entryPath);
    if ($stat === false) {
        $zip->close();
        send_not_found();
    }

    $stream = $zip->getStream($entryPath);
    if ($stream === false) {
        $zip->close();
        send_not_found();
    }

    $fileName = basename($entryPath);
    $mime = 'application/octet-stream';
    $ext = strtolower((string)pathinfo($fileName, PATHINFO_EXTENSION));
    $mimeMap = [
        'png' => 'image/png',
        'jpg' => 'image/jpeg',
        'jpeg' => 'image/jpeg',
        'gif' => 'image/gif',
        'webp' => 'image/webp',
        'pdf' => 'application/pdf',
        'txt' => 'text/plain',
    ];
    if (isset($mimeMap[$ext])) {
        $mime = $mimeMap[$ext];
    }

    header('Content-Type: ' . $mime);
    header('Content-Length: ' . (string)($stat['size'] ?? 0));
    if ($download) {
        header('Content-Disposition: attachment; filename="' . rawurlencode($fileName) . '"');
    } else {
        header('Content-Disposition: inline; filename="' . rawurlencode($fileName) . '"');
    }

    while (!feof($stream)) {
        echo fread($stream, 8192);
    }

    fclose($stream);
    $zip->close();
    exit;
}

function is_image_attachment(array $att): bool {
    $name = (string)($att['name'] ?? '');
    if ($name === '') {
        $name = (string)($att['saved_as'] ?? '');
    }
    $ext = strtolower((string)pathinfo($name, PATHINFO_EXTENSION));
    return in_array($ext, ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'avif'], true);
}

function render_rich_text(string $html): string {
    if ($html === '') {
        return '';
    }
    $allowed = '<body><a><p><br><strong><em><ul><ol><li><img><blockquote><code><pre><span><div>';
    $clean = strip_tags($html, $allowed);
    $clean = preg_replace('/\son[a-z]+\s*=\s*"[^"]*"/i', '', (string)$clean);
    $clean = preg_replace('/\son[a-z]+\s*=\s*\'[^\']*\'/i', '', (string)$clean);
    $clean = preg_replace('/\sjavascript:/i', ' ', (string)$clean);
    return nl2br((string)$clean, false);
}

$envVars = load_env_vars($envFile);
$authUsername = trim((string)($envVars['APP_USERNAME'] ?? ''));
$authPassword = (string)($envVars['APP_PASSWORD'] ?? '');
$authEnabled = $authUsername !== '' && $authPassword !== '';

if ($route === 'logout') {
    $_SESSION = [];
    if (session_status() === PHP_SESSION_ACTIVE) {
        session_destroy();
    }
    header('Location: /login');
    exit;
}

$isAuthenticated = !$authEnabled || (bool)($_SESSION['is_authenticated'] ?? false);

if ($route === 'login') {
    if (!$authEnabled) {
        header('Location: /');
        exit;
    }

    if ($isAuthenticated) {
        header('Location: /');
        exit;
    }

    $maxFailedAttempts = 5;
    $attemptWindowSeconds = 15 * 60;
    $lockoutSeconds = 15 * 60;
    $now = time();
    $ip = client_ip();
    $attempts = auth_attempts_read($authAttemptsFile);
    $entry = auth_attempt_entry($attempts, $ip, $now, $attemptWindowSeconds);

    if ($entry['locked_until'] > $now) {
        render_login_page(auth_lockout_message($entry['locked_until'] - $now));
    }

    $attempts[$ip] = $entry;

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $username = trim((string)($_POST['username'] ?? ''));
        $password = (string)($_POST['password'] ?? '');
        if (hash_equals($authUsername, $username) && hash_equals($authPassword, $password)) {
            session_regenerate_id(true);
            $_SESSION['is_authenticated'] = true;
            $_SESSION['auth_username'] = $authUsername;
            unset($attempts[$ip]);
            auth_attempts_write($authAttemptsFile, $attempts);
            header('Location: /');
            exit;
        }

        $entry['failures'][] = $now;
        $entry['failures'] = array_values(array_filter(
            $entry['failures'],
            static fn (int $ts): bool => $ts >= ($now - $attemptWindowSeconds)
        ));

        if (count($entry['failures']) >= $maxFailedAttempts) {
            $entry['failures'] = [];
            $entry['locked_until'] = $now + $lockoutSeconds;
            $attempts[$ip] = $entry;
            auth_attempts_write($authAttemptsFile, $attempts);
            render_login_page(auth_lockout_message($lockoutSeconds));
        }

        $attempts[$ip] = $entry;
        auth_attempts_write($authAttemptsFile, $attempts);
        $remaining = max(0, $maxFailedAttempts - count($entry['failures']));
        $suffix = $remaining > 0 ? ' Attempts left before lockout: ' . $remaining . '.' : '';
        render_login_page('Invalid username or password.' . $suffix);
    }

    render_login_page();
}

if (!$isAuthenticated) {
    render_restricted_page();
}

$index = json_read($dataFile);
$projects = $index['projects'] ?? [];
$lastRun = json_read($lastRunFile);
$isViewerPageRoute = preg_match('#^view/[a-z0-9-]+/[^/]+(?:/task/[0-9]+)?$#', $route) === 1;

if (preg_match('#^download/([a-z0-9-]+)/(.+)$#', $route, $m)) {
    $projectSlug = $m[1];
    $fileName = basename($m[2]);
    if (!preg_match('/\.zip$/i', $fileName)) {
        send_not_found();
    }

    $project = find_project($projects, $projectSlug);
    if ($project === null || find_backup($project, $fileName) === null) {
        send_not_found();
    }

    $fullPath = $webRoot . '/files/' . $projectSlug . '/' . $fileName;
    if (!is_file($fullPath)) {
        send_not_found();
    }

    header('Content-Type: application/zip');
    header('Content-Length: ' . (string)filesize($fullPath));
    header('Content-Disposition: attachment; filename="' . rawurlencode($fileName) . '"');
    readfile($fullPath);
    exit;
}

if (preg_match('#^report/([a-z0-9-]+)/([^/]+)$#', $route, $m)) {
    $projectSlug = $m[1];
    $zipFile = basename($m[2]);
    if (!preg_match('/\.zip$/i', $zipFile)) {
        send_not_found();
    }

    $project = find_project($projects, $projectSlug);
    if ($project === null || find_backup($project, $zipFile) === null) {
        send_not_found();
    }

    $zipPath = $webRoot . '/files/' . $projectSlug . '/' . $zipFile;
    if (!is_file($zipPath)) {
        send_not_found();
    }

    $statusCounts = list_zip_status_counts($zipPath);
    $preferredStatuses = [
        'Client to verify',
        'Open',
        'Closed',
        'Fix In Progress',
        'Out of Scope',
        'QA to verify',
    ];

    $rows = [];
    $usedStatuses = [];
    foreach ($preferredStatuses as $statusName) {
        $count = (int)($statusCounts[$statusName] ?? 0);
        if ($count <= 0) {
            $usedStatuses[$statusName] = true;
            continue;
        }
        $rows[] = [
            'status' => $statusName,
            'count' => $count,
        ];
        $usedStatuses[$statusName] = true;
    }

    $extraStatuses = [];
    foreach ($statusCounts as $statusName => $count) {
        if (isset($usedStatuses[$statusName])) {
            continue;
        }
        if ((int)$count <= 0) {
            continue;
        }
        $extraStatuses[] = [
            'status' => (string)$statusName,
            'count' => (int)$count,
        ];
    }
    usort($extraStatuses, static function (array $a, array $b): int {
        return strnatcasecmp((string)($a['status'] ?? ''), (string)($b['status'] ?? ''));
    });

    foreach ($extraStatuses as $statusRow) {
        $rows[] = $statusRow;
    }

    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['rows' => $rows], JSON_UNESCAPED_SLASHES);
    exit;
}

if (preg_match('#^view/([a-z0-9-]+)/([^/]+)/(attachment|attachment-preview|inline)/([0-9]+)/([0-9]+)$#', $route, $m)) {
    $projectSlug = $m[1];
    $zipFile = basename($m[2]);
    $assetType = $m[3];
    $taskGid = $m[4];
    $indexNum = (int)$m[5];

    if (!preg_match('/\.zip$/i', $zipFile) || $indexNum < 1) {
        send_not_found();
    }

    $project = find_project($projects, $projectSlug);
    if ($project === null || find_backup($project, $zipFile) === null) {
        send_not_found();
    }

    $zipPath = $webRoot . '/files/' . $projectSlug . '/' . $zipFile;
    if (!is_file($zipPath)) {
        send_not_found();
    }

    $metaEntry = in_array($assetType, ['attachment', 'attachment-preview'], true)
        ? 'attachments/' . $taskGid . '/_meta.json'
        : 'inline-assets/' . $taskGid . '/_meta.json';

    $zip = open_zip($zipPath);
    $meta = zip_json($zip, $metaEntry);
    $zip->close();
    if (!isset($meta[$indexNum - 1]) || !is_array($meta[$indexNum - 1])) {
        send_not_found();
    }
    $item = $meta[$indexNum - 1];
    $savedAs = (string)($item['saved_as'] ?? '');
    if ($savedAs === '') {
        send_not_found();
    }
    stream_zip_entry($zipPath, $savedAs, $assetType !== 'attachment-preview');
}

?><!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Asana Backups</title>
  <style>
    body { font-family: Georgia, "Times New Roman", serif; width: 100%; margin: 0; padding: 1.25rem; box-sizing: border-box; background: #f7f4ee; color: #1f1a12; }
    a { color: #7d2b1f; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .card { background: #fffdf8; border: 1px solid #ddd2bf; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .muted { color: #6d5f4e; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #eee2cf; text-align: left; padding: 0.55rem; }
    .board-wrap { display: flex; gap: 0.9rem; align-items: stretch; overflow-x: auto; overflow-y: hidden; padding: 0.5rem; border: 1px solid #ddd2bf; border-radius: 8px; background: #f6f0e6; cursor: grab; scroll-behavior: smooth; }
    .board-wrap.dragging { cursor: grabbing; user-select: none; }
    .board-col { background: #fffdf8; border: 1px solid #ddd2bf; border-radius: 8px; padding: 0.85rem; flex: 0 0 320px; max-width: 320px; }
    .board-tasks { overflow: visible; }
    .task-item { border: 1px solid #efe3d0; border-radius: 6px; padding: 0.6rem; margin-bottom: 0.55rem; background: #fff; }
    .task-item.done { border-color: #9fd0ab; background: linear-gradient(180deg, #f3fff3 0%, #e7f8e9 100%); }
    .task-item.done a { color: #1f6b3a; }
    .rich img { max-width: 100%; height: auto; display: block; margin: 0.7rem auto; }
    .comment { border-top: 1px solid #efe3d0; padding-top: 0.75rem; margin-top: 0.75rem; }
    .tag { display: inline-block; padding: 0.18rem 0.45rem; border-radius: 999px; background: #f0e4d2; color: #6b4c2a; font-size: 0.8rem; }
    .attachment-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.75rem; }
    .attachment-tile { border: 1px solid #e8dac4; border-radius: 8px; background: #fff; padding: 0.45rem; cursor: pointer; text-align: left; }
    .attachment-thumb { width: 100%; height: 120px; border-radius: 6px; object-fit: cover; background: #f4ede0; display: block; }
    .attachment-icon { width: 100%; height: 120px; border-radius: 6px; background: #f4ede0; color: #7f7568; display: flex; align-items: center; justify-content: center; font-size: 2rem; }
    .attachment-name { margin-top: 0.4rem; font-size: 0.85rem; color: #443829; overflow-wrap: anywhere; }
    .lightbox { position: fixed; inset: 0; background: rgba(15, 12, 7, 0.86); display: none; align-items: center; justify-content: center; z-index: 9999; }
    .lightbox.open { display: flex; }
    .lightbox-panel { width: min(92vw, 1100px); max-height: 90vh; background: #fffdf8; border-radius: 10px; padding: 0.8rem; border: 1px solid #decfb7; }
    .lightbox-head { display: flex; align-items: center; justify-content: space-between; gap: 0.7rem; margin-bottom: 0.55rem; }
    .lightbox-title { font-size: 0.9rem; color: #3b2f1f; overflow-wrap: anywhere; }
    .lightbox-actions a, .lightbox-actions button { border: 1px solid #d8c9b2; background: #fff; color: #5c3a1f; border-radius: 6px; padding: 0.35rem 0.6rem; cursor: pointer; }
    .lightbox-body { position: relative; min-height: 300px; max-height: 76vh; display: flex; align-items: center; justify-content: center; background: #f8f2e8; border-radius: 8px; overflow: hidden; }
    .lightbox-media { max-width: 100%; max-height: 75vh; display: block; }
    .lightbox-file { width: 220px; height: 220px; border-radius: 16px; background: #f0e6d7; color: #7d6b55; display: flex; align-items: center; justify-content: center; flex-direction: column; }
    .lightbox-file span { font-size: 3rem; line-height: 1; }
    .lightbox-nav { position: absolute; top: 50%; transform: translateY(-50%); border: 0; background: rgba(255,255,255,0.85); color: #473621; border-radius: 999px; width: 36px; height: 36px; cursor: pointer; }
    .lightbox-nav.left { left: 10px; }
    .lightbox-nav.right { right: 10px; }
    .view-actions { display: flex; gap: 0.6rem; align-items: center; margin: 0.7rem 0 0.9rem; flex-wrap: wrap; }
    .btn { display: inline-block; border: 1px solid #d8c9b2; background: #fff; color: #5c3a1f; border-radius: 6px; padding: 0.45rem 0.75rem; text-decoration: none; }
    .btn:hover { text-decoration: none; background: #f9f2e6; }
    .search-input { border: 1px solid #d8c9b2; background: #fff; color: #3b2f1f; border-radius: 6px; padding: 0.45rem 0.75rem; min-width: 260px; }
    .scroll-btn { min-width: 38px; text-align: center; padding: 0.45rem 0.65rem; }
    .board-top { position: sticky; top: 0; z-index: 20; background: #f7f4ee; padding: 0.2rem 0 0.35rem; }
    .task-title { margin: 0 0 0.2rem; }
    .task-subtitle { margin: 0 0 0.85rem; }
    .report-modal { position: fixed; inset: 0; background: rgba(15, 12, 7, 0.64); display: none; align-items: center; justify-content: center; z-index: 10000; padding: 1rem; box-sizing: border-box; }
    .report-modal.open { display: flex; }
    .report-panel { width: min(560px, 100%); max-height: 90vh; overflow: auto; background: #fffdf8; border: 1px solid #decfb7; border-radius: 10px; padding: 0.9rem; box-sizing: border-box; }
    .report-head { display: flex; align-items: center; justify-content: space-between; gap: 0.7rem; margin-bottom: 0.7rem; }
    .report-title { margin: 0; }
    .report-meta { margin: 0.35rem 0 0.8rem; }
    .report-close-btn { cursor: pointer; }
    .report-table th:nth-child(2), .report-table td:nth-child(2) { text-align: center; }
  </style>
</head>
<body>
  <h1>Asana Backup Files</h1>
  <?php if ($authEnabled): ?>
    <div class="card">
      Signed in as <strong><?= h((string)($_SESSION['auth_username'] ?? 'user')) ?></strong>
      <a class="btn" style="margin-left:0.55rem;" href="/logout">Logout</a>
    </div>
  <?php endif; ?>
  <?php if ($route === '' && !$isViewerPageRoute && !empty($lastRun)): ?>
    <div class="card">
      <strong>Last Run:</strong> <?= h(format_datetime((string)($lastRun['generated_at'] ?? ''))) ?>
      <br>
      <span class="muted">Success: <?= h((string)($lastRun['success_count'] ?? '0')) ?> | Failed: <?= h((string)($lastRun['failure_count'] ?? '0')) ?></span>
    </div>
  <?php endif; ?>

  <?php
  if ($route === ''):
  ?>
    <?php if (empty($projects)): ?>
      <div class="card">No backup index yet. Run the backup job first.</div>
    <?php else: ?>
      <?php foreach ($projects as $project): ?>
        <?php
          $slug = (string)($project['project_slug'] ?? '');
          $name = (string)($project['project_name'] ?? $slug);
          $gid = (string)($project['project_gid'] ?? '');
          $count = is_array($project['backups'] ?? null) ? count($project['backups']) : 0;
        ?>
        <div class="card">
          <h3 style="margin-top:0;"><a href="/project/<?= h($slug) ?>"><?= h($name) ?> - GID: <?= h($gid) ?></a></h3>
          <div class="muted">Backups: <?= h((string)$count) ?></div>
        </div>
      <?php endforeach; ?>
    <?php endif; ?>
  <?php elseif (preg_match('#^project/([a-z0-9-]+)$#', $route, $m)): ?>
    <?php
      $projectSlug = $m[1];
      $selected = null;
      foreach ($projects as $project) {
          if (($project['project_slug'] ?? '') === $projectSlug) {
              $selected = $project;
              break;
          }
      }
      if (!$selected) {
          send_not_found();
      }
      $backups = is_array($selected['backups'] ?? null) ? $selected['backups'] : [];
    ?>
    <p><a class="btn" href="/">&larr; Back to projects</a></p>
    <h2><?= h((string)$selected['project_name']) ?> - GID: <?= h((string)$selected['project_gid']) ?></h2>
    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>File</th>
            <th>Download</th>
            <th>View</th>
            <th>Report</th>
            <th>Size</th>
            <th>Task Count</th>
          </tr>
        </thead>
        <tbody>
        <?php foreach ($backups as $row): ?>
          <tr>
            <td><?= h(format_run_stamp((string)($row['run_stamp'] ?? ''))) ?></td>
            <td><a href="/view/<?= h($projectSlug) ?>/<?= h((string)$row['zip_file']) ?>"><?= h((string)$row['zip_file']) ?></a></td>
            <td><a class="btn" href="/download/<?= h($projectSlug) ?>/<?= h((string)$row['zip_file']) ?>">Download</a></td>
            <td><a class="btn" href="/view/<?= h($projectSlug) ?>/<?= h((string)$row['zip_file']) ?>">Open</a></td>
            <td><button type="button" class="btn report-btn" data-report-url="/report/<?= h($projectSlug) ?>/<?= h((string)$row['zip_file']) ?>" data-report-label="<?= h((string)$row['zip_file']) ?>">View</button></td>
            <td><?= h(format_bytes((int)($row['zip_size'] ?? 0))) ?></td>
            <td><?= h((string)($row['counts']['tasks'] ?? '0')) ?></td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table>
    </div>

    <div id="reportModal" class="report-modal" aria-hidden="true">
      <div class="report-panel" role="dialog" aria-modal="true" aria-labelledby="reportTitle">
        <div class="report-head">
          <h3 id="reportTitle" class="report-title">Ticket Report</h3>
          <button type="button" id="reportClose" class="btn report-close-btn">Close</button>
        </div>
        <div id="reportMeta" class="muted report-meta"></div>
        <table class="report-table">
          <thead>
            <tr>
              <th>Case Status</th>
              <th>Task Count</th>
            </tr>
          </thead>
          <tbody id="reportRows">
            <tr>
              <td class="muted" colspan="2">Click a View button to load report.</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <th>Total</th>
              <th id="reportTotal">0</th>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  <?php elseif (preg_match('#^view/([a-z0-9-]+)/([^/]+)$#', $route, $m)): ?>
    <?php
      $projectSlug = $m[1];
      $zipFile = basename($m[2]);
      if (!preg_match('/\.zip$/i', $zipFile)) {
          send_not_found();
      }

      $project = find_project($projects, $projectSlug);
      if ($project === null || find_backup($project, $zipFile) === null) {
          send_not_found();
      }

      $zipPath = $webRoot . '/files/' . $projectSlug . '/' . $zipFile;
      if (!is_file($zipPath)) {
          send_not_found();
      }

      $hideCompleted = (string)($_GET['hide_completed'] ?? '0') === '1';
      $payload = list_zip_backup_data($zipPath);
      $tasks = $payload['tasks'];
      $boards = $payload['boards'];
    ?>
    <div class="board-top">
      <p><a class="btn" href="/project/<?= h($projectSlug) ?>">&larr; Back to project backups</a></p>
      <h2>Task Board View</h2>
      <div class="view-actions">
        <a class="btn" href="/download/<?= h($projectSlug) ?>/<?= h($zipFile) ?>">Download ZIP</a>
        <?php if ($hideCompleted): ?>
          <a class="btn" href="/view/<?= h($projectSlug) ?>/<?= h($zipFile) ?>?hide_completed=0">Show completed tasks</a>
        <?php else: ?>
          <a class="btn" href="/view/<?= h($projectSlug) ?>/<?= h($zipFile) ?>?hide_completed=1">Hide completed tasks</a>
        <?php endif; ?>
        <button id="scrollLeftBtn" type="button" class="btn scroll-btn" aria-label="Scroll boards left">&lt;</button>
        <button id="scrollRightBtn" type="button" class="btn scroll-btn" aria-label="Scroll boards right">&gt;</button>
        <input id="taskSearch" class="search-input" type="search" placeholder="Search task name, GID, creator..." autocomplete="off">
      </div>
    </div>

    <div class="board-wrap" id="boardWrap">
      <?php foreach ($boards as $board): ?>
        <?php
          $section = (string)($board['name'] ?? 'Unsectioned');
          $taskIds = is_array($board['task_ids'] ?? null) ? $board['task_ids'] : [];
          $visible = [];
          foreach ($taskIds as $taskGid) {
              $task = $tasks[$taskGid] ?? null;
              if (!is_array($task)) {
                  continue;
              }
              if ($hideCompleted && !empty($task['completed'])) {
                  continue;
              }
              $visible[] = $task;
          }
        ?>
        <div class="board-col">
          <h3 style="margin-top:0;"><?= h((string)$section) ?> <span class="tag board-count"><?= h((string)count($visible)) ?></span></h3>
          <div class="board-tasks">
            <?php if (empty($visible)): ?>
              <div class="muted">No tasks in this filter.</div>
            <?php else: ?>
              <?php foreach ($visible as $task): ?>
                <?php
                  $taskGid = (string)($task['gid'] ?? '');
                  $done = !empty($task['completed']);
                  $searchText = implode(' ', [
                      (string)($task['name'] ?? ''),
                      $taskGid,
                      task_creator_label($task),
                      (string)($task['notes'] ?? ''),
                  ]);
                ?>
                <div class="task-item <?= $done ? 'done' : '' ?>" data-search="<?= h($searchText) ?>">
                  <div><a href="/view/<?= h($projectSlug) ?>/<?= h($zipFile) ?>/task/<?= h($taskGid) ?>"><?= h((string)($task['name'] ?? $taskGid)) ?></a></div>
                  <div class="muted" style="font-size:0.85rem;">Task: <?= h($taskGid) ?><?= $done ? ' | completed' : '' ?></div>
                  <div class="muted" style="font-size:0.82rem;">Creator: <?= h(task_creator_label($task)) ?></div>
                  <div class="muted" style="font-size:0.82rem;">Created: <?= h(format_datetime((string)($task['created_at'] ?? ''))) ?></div>
                  <div class="muted" style="font-size:0.82rem;">Last Modified: <?= h(format_datetime((string)($task['modified_at'] ?? ''))) ?></div>
                </div>
              <?php endforeach; ?>
              <?php endif; ?>
            </div>
          </div>
      <?php endforeach; ?>
    </div>
  <?php elseif (preg_match('#^view/([a-z0-9-]+)/([^/]+)/task/([0-9]+)$#', $route, $m)): ?>
    <?php
      $projectSlug = $m[1];
      $zipFile = basename($m[2]);
      $taskGid = $m[3];
      if (!preg_match('/\.zip$/i', $zipFile)) {
          send_not_found();
      }

      $project = find_project($projects, $projectSlug);
      if ($project === null || find_backup($project, $zipFile) === null) {
          send_not_found();
      }

      $zipPath = $webRoot . '/files/' . $projectSlug . '/' . $zipFile;
      if (!is_file($zipPath)) {
          send_not_found();
      }

      $payload = list_zip_backup_data($zipPath);
      $task = $payload['tasks'][$taskGid] ?? null;
      if (!is_array($task)) {
          send_not_found();
      }
      $comments = is_array($payload['comments'][$taskGid] ?? null) ? $payload['comments'][$taskGid] : [];
      $attachments = is_array($payload['attachments'][$taskGid] ?? null) ? $payload['attachments'][$taskGid] : [];
      $descriptionHtml = (string)($task['html_notes'] ?? '');
      $descriptionText = (string)($task['notes'] ?? '');
      $descriptionHtml = rewrite_asana_asset_links($descriptionHtml, $projectSlug, $zipFile, $taskGid, $attachments);
    ?>
    <p><a class="btn" href="/view/<?= h($projectSlug) ?>/<?= h($zipFile) ?>">&larr; Back to board view</a></p>
    <h2 class="task-title"><?= h((string)($task['name'] ?? $taskGid)) ?></h2>
    <div class="muted task-subtitle"><?= h(task_group_label($task)) ?></div>
    <div class="muted">Task GID: <?= h($taskGid) ?><?= !empty($task['completed']) ? ' | completed' : '' ?></div>

    <div class="card">
      <h3 style="margin-top:0;">Description</h3>
      <?php if ($descriptionHtml !== ''): ?>
        <div class="rich"><?= render_rich_text($descriptionHtml) ?></div>
      <?php elseif ($descriptionText !== ''): ?>
        <pre style="white-space:pre-wrap;"><?= h($descriptionText) ?></pre>
      <?php else: ?>
        <div class="muted">No description.</div>
      <?php endif; ?>
    </div>

    <div class="card">
      <h3 style="margin-top:0;">Task Attachments</h3>
      <?php if (empty($attachments)): ?>
        <div class="muted">No attachments.</div>
      <?php else: ?>
        <div class="attachment-grid">
          <?php foreach ($attachments as $idx => $att): ?>
            <?php
              $hasFile = !empty($att['saved_as']);
              $name = (string)($att['name'] ?? ($hasFile ? basename((string)$att['saved_as']) : 'Attachment'));
              $isImage = $hasFile && is_image_attachment(is_array($att) ? $att : []);
              $downloadUrl = '/view/' . h($projectSlug) . '/' . h($zipFile) . '/attachment/' . h($taskGid) . '/' . h((string)($idx + 1));
              $previewUrl = '/view/' . h($projectSlug) . '/' . h($zipFile) . '/attachment-preview/' . h($taskGid) . '/' . h((string)($idx + 1));
            ?>
            <button
              type="button"
              class="attachment-tile"
              <?= $hasFile ? '' : 'disabled' ?>
              data-lightbox-item="1"
              data-index="<?= h((string)$idx) ?>"
              data-name="<?= h($name) ?>"
              data-image="<?= $isImage ? '1' : '0' ?>"
              data-preview-url="<?= $hasFile ? $previewUrl : '' ?>"
              data-download-url="<?= $hasFile ? $downloadUrl : '' ?>"
            >
              <?php if ($isImage): ?>
                <img src="<?= $previewUrl ?>" alt="<?= h($name) ?>" class="attachment-thumb">
              <?php else: ?>
                <div class="attachment-icon">&#128196;</div>
              <?php endif; ?>
              <div class="attachment-name"><?= h($name) ?><?= $hasFile ? '' : ' (not downloaded)' ?></div>
            </button>
          <?php endforeach; ?>
        </div>

        <div id="attachmentLightbox" class="lightbox" aria-hidden="true">
          <div class="lightbox-panel">
            <div class="lightbox-head">
              <div id="lightboxTitle" class="lightbox-title"></div>
              <div class="lightbox-actions">
                <a id="lightboxDownload" href="#" download>Download</a>
                <button type="button" id="lightboxClose">Close</button>
              </div>
            </div>
            <div class="lightbox-body" id="lightboxBody">
              <button type="button" class="lightbox-nav left" id="lightboxPrev" aria-label="Previous">&#8592;</button>
              <button type="button" class="lightbox-nav right" id="lightboxNext" aria-label="Next">&#8594;</button>
            </div>
          </div>
        </div>
      <?php endif; ?>
    </div>

    <div class="card">
      <h3 style="margin-top:0;">Comments</h3>
      <?php if (empty($comments)): ?>
        <div class="muted">No comments.</div>
      <?php else: ?>
        <?php foreach ($comments as $comment): ?>
          <div class="comment">
            <div style="margin-bottom:0.4rem;">
              <strong><?= h((string)($comment['created_by']['name'] ?? 'Unknown')) ?></strong>
              <span class="muted"> - <?= h((string)($comment['created_at'] ?? '')) ?></span>
            </div>
            <?php $htmlText = (string)($comment['html_text'] ?? ''); ?>
            <?php if ($htmlText !== ''): ?>
              <div class="rich"><?= render_rich_text(rewrite_asana_asset_links($htmlText, $projectSlug, $zipFile, $taskGid, $attachments)) ?></div>
            <?php else: ?>
              <pre style="white-space:pre-wrap;"><?= h((string)($comment['text'] ?? '')) ?></pre>
            <?php endif; ?>
          </div>
        <?php endforeach; ?>
      <?php endif; ?>
    </div>
  <?php else: ?>
    <?php send_not_found(); ?>
  <?php endif; ?>
  <script>
    (function () {
      var boardWrap = document.getElementById('boardWrap');
      if (boardWrap) {
        var isDown = false;
        var startX = 0;
        var startScrollLeft = 0;
        var scrollLeftBtn = document.getElementById('scrollLeftBtn');
        var scrollRightBtn = document.getElementById('scrollRightBtn');

        boardWrap.addEventListener('mousedown', function (event) {
          if (event.button !== 0) {
            return;
          }
          isDown = true;
          boardWrap.classList.add('dragging');
          startX = event.pageX;
          startScrollLeft = boardWrap.scrollLeft;
        });

        window.addEventListener('mouseup', function () {
          isDown = false;
          boardWrap.classList.remove('dragging');
        });

        boardWrap.addEventListener('mouseleave', function () {
          isDown = false;
          boardWrap.classList.remove('dragging');
        });

        boardWrap.addEventListener('mousemove', function (event) {
          if (!isDown) {
            return;
          }
          event.preventDefault();
          var moved = (event.pageX - startX) * 1.2;
          boardWrap.scrollLeft = startScrollLeft - moved;
        });

        if (scrollLeftBtn) {
          scrollLeftBtn.addEventListener('click', function () {
            boardWrap.scrollBy({ left: -360, behavior: 'smooth' });
          });
        }
        if (scrollRightBtn) {
          scrollRightBtn.addEventListener('click', function () {
            boardWrap.scrollBy({ left: 360, behavior: 'smooth' });
          });
        }
      }

      var searchInput = document.getElementById('taskSearch');
      if (searchInput) {
        var boardCols = Array.prototype.slice.call(document.querySelectorAll('.board-col'));
        var taskCards = Array.prototype.slice.call(document.querySelectorAll('.task-item[data-search]'));

        var applyTaskFilter = function () {
          var keyword = (searchInput.value || '').trim().toLowerCase();
          taskCards.forEach(function (card) {
            var text = (card.getAttribute('data-search') || '').toLowerCase();
            var matched = keyword === '' || text.indexOf(keyword) !== -1;
            card.style.display = matched ? '' : 'none';
          });

          boardCols.forEach(function (col) {
            var visibleCount = 0;
            var colCards = col.querySelectorAll('.task-item[data-search]');
            Array.prototype.forEach.call(colCards, function (card) {
              if (card.style.display !== 'none') {
                visibleCount += 1;
              }
            });
            var countEl = col.querySelector('.board-count');
            if (countEl) {
              countEl.textContent = String(visibleCount);
            }
          });
        };

        searchInput.addEventListener('input', applyTaskFilter);
      }

      var reportModal = document.getElementById('reportModal');
      if (reportModal) {
        var reportButtons = Array.prototype.slice.call(document.querySelectorAll('.report-btn[data-report-url]'));
        var reportRows = document.getElementById('reportRows');
        var reportMeta = document.getElementById('reportMeta');
        var reportTotal = document.getElementById('reportTotal');
        var reportClose = document.getElementById('reportClose');

        function closeReportModal() {
          reportModal.classList.remove('open');
          reportModal.setAttribute('aria-hidden', 'true');
        }

        function setReportRows(contentRows) {
          reportRows.innerHTML = '';
          var total = 0;
          contentRows.forEach(function (row) {
            var tr = document.createElement('tr');
            var statusTd = document.createElement('td');
            var countTd = document.createElement('td');
            statusTd.textContent = row.status;
            countTd.textContent = String(row.count);
            total += Number(row.count) || 0;
            tr.appendChild(statusTd);
            tr.appendChild(countTd);
            reportRows.appendChild(tr);
          });
          if (reportTotal) {
            reportTotal.textContent = String(total);
          }
        }

        function showReportMessage(message) {
          reportRows.innerHTML = '';
          var tr = document.createElement('tr');
          var td = document.createElement('td');
          td.colSpan = 2;
          td.className = 'muted';
          td.textContent = message;
          tr.appendChild(td);
          reportRows.appendChild(tr);
          if (reportTotal) {
            reportTotal.textContent = '0';
          }
        }

        function openReportModal(button) {
          var reportUrl = button.getAttribute('data-report-url') || '';
          var reportLabel = button.getAttribute('data-report-label') || '';

          reportMeta.textContent = reportLabel ? 'Backup: ' + reportLabel : '';
          showReportMessage('Loading report...');
          reportModal.classList.add('open');
          reportModal.setAttribute('aria-hidden', 'false');

          if (!reportUrl) {
            showReportMessage('Report URL is missing.');
            return;
          }

          fetch(reportUrl, { headers: { 'Accept': 'application/json' } })
            .then(function (response) {
              if (!response.ok) {
                throw new Error('Request failed');
              }
              return response.json();
            })
            .then(function (payload) {
              var rows = Array.isArray(payload.rows) ? payload.rows : [];
              if (rows.length === 0) {
                showReportMessage('No status data found.');
                return;
              }
              setReportRows(rows);
            })
            .catch(function () {
              showReportMessage('Unable to load report right now.');
            });
        }

        reportButtons.forEach(function (button) {
          button.addEventListener('click', function () {
            openReportModal(button);
          });
        });

        if (reportClose) {
          reportClose.addEventListener('click', closeReportModal);
        }
      }

      var items = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox-item="1"]'));
      var lightbox = document.getElementById('attachmentLightbox');
      if (lightbox && items.length > 0) {
        var lightboxBody = document.getElementById('lightboxBody');
        var titleEl = document.getElementById('lightboxTitle');
        var downloadEl = document.getElementById('lightboxDownload');
        var closeEl = document.getElementById('lightboxClose');
        var prevEl = document.getElementById('lightboxPrev');
        var nextEl = document.getElementById('lightboxNext');
        var current = 0;

        function renderLightbox(index) {
          if (index < 0) {
            index = items.length - 1;
          }
          if (index >= items.length) {
            index = 0;
          }
          current = index;

          var item = items[current];
          var name = item.getAttribute('data-name') || 'Attachment';
          var isImage = item.getAttribute('data-image') === '1';
          var previewUrl = item.getAttribute('data-preview-url') || '';
          var downloadUrl = item.getAttribute('data-download-url') || '';

          titleEl.textContent = (current + 1) + ' / ' + items.length + ' - ' + name;
          downloadEl.setAttribute('href', downloadUrl || '#');
          downloadEl.style.visibility = downloadUrl ? 'visible' : 'hidden';

          var oldMedia = document.getElementById('lightboxMediaSlot');
          if (oldMedia) {
            oldMedia.remove();
          }

          var mediaSlot = document.createElement('div');
          mediaSlot.id = 'lightboxMediaSlot';
          if (isImage && previewUrl) {
            var img = document.createElement('img');
            img.src = previewUrl;
            img.alt = name;
            img.className = 'lightbox-media';
            mediaSlot.appendChild(img);
          } else {
            var fileBox = document.createElement('div');
            fileBox.className = 'lightbox-file';
            var icon = document.createElement('span');
            icon.textContent = '\uD83D\uDCC4';
            var txt = document.createElement('div');
            txt.textContent = 'Preview not available';
            fileBox.appendChild(icon);
            fileBox.appendChild(txt);
            mediaSlot.appendChild(fileBox);
          }
          lightboxBody.appendChild(mediaSlot);
        }

        function openLightbox(index) {
          renderLightbox(index);
          lightbox.classList.add('open');
          lightbox.setAttribute('aria-hidden', 'false');
        }

        function closeLightbox() {
          lightbox.classList.remove('open');
          lightbox.setAttribute('aria-hidden', 'true');
        }

        items.forEach(function (item, index) {
          item.addEventListener('click', function () {
            if (item.disabled) {
              return;
            }
            openLightbox(index);
          });
        });

        prevEl.addEventListener('click', function (event) {
          event.stopPropagation();
          renderLightbox(current - 1);
        });
        nextEl.addEventListener('click', function (event) {
          event.stopPropagation();
          renderLightbox(current + 1);
        });
        closeEl.addEventListener('click', closeLightbox);

        lightbox.addEventListener('click', function (event) {
          if (event.target === lightbox) {
            closeLightbox();
          }
        });

        document.addEventListener('keydown', function (event) {
          if (!lightbox.classList.contains('open')) {
            return;
          }
          if (event.key === 'Escape') {
            closeLightbox();
            return;
          }
          if (event.key === 'ArrowLeft') {
            renderLightbox(current - 1);
            return;
          }
          if (event.key === 'ArrowRight') {
            renderLightbox(current + 1);
          }
        });
      }
    })();
  </script>
</body>
</html>
