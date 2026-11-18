<?php
declare(strict_types=1);

/**
 * Builds the /reporting XLSX rows from the Task Manager project export and
 * task detail endpoints.
 */

function tm_report_format_date(string $isoDate): string
{
    if ($isoDate === '') {
        return '';
    }
    try {
        $dt = new DateTimeImmutable($isoDate);
        return $dt->format('M j, Y');
    } catch (Exception $e) {
        return $isoDate;
    }
}

function tm_report_days_between(string $startIso, string $endIso): string
{
    if ($startIso === '' || $endIso === '') {
        return '';
    }
    $startTs = strtotime($startIso);
    $endTs = strtotime($endIso);
    if ($startTs === false || $endTs === false) {
        return '';
    }
    return (string)max(0, (int)floor(($endTs - $startTs) / 86400));
}

function tm_report_strip_file_names(string $text): string
{
    if ($text === '') {
        return '';
    }
    $text = preg_replace('/https?:\/\/\S+/i', ' ', $text);
    $text = preg_replace('/\b[^\s]+\.(?:pdf|png|jpg|jpeg|gif|webp|bmp|svg|doc|docx|xls|xlsx|csv|zip|rar|7z|ppt|pptx|txt|mov|mp4)\b/i', ' ', (string)$text);
    return trim((string)preg_replace('/\s+/u', ' ', (string)$text));
}

function tm_report_parse_csv(string $csv): array
{
    $tmp = fopen('php://temp', 'r+');
    if ($tmp === false) {
        throw new RuntimeException('Unable to read Task Manager CSV export.');
    }
    fwrite($tmp, $csv);
    rewind($tmp);

    $headers = fgetcsv($tmp);
    if (!is_array($headers)) {
        fclose($tmp);
        return [];
    }
    $headers = array_map(static fn($h): string => trim((string)$h), $headers);
    if (isset($headers[0]) && str_starts_with($headers[0], "\xEF\xBB\xBF")) {
        $headers[0] = substr($headers[0], 3);
    }

    $rows = [];
    while (($data = fgetcsv($tmp)) !== false) {
        if (!is_array($data) || ($data === [null])) {
            continue;
        }
        $row = [];
        foreach ($headers as $index => $header) {
            if ($header === '') {
                continue;
            }
            $row[$header] = (string)($data[$index] ?? '');
        }
        $rows[] = $row;
    }
    fclose($tmp);
    return $rows;
}

function tm_report_collect_text($node, array &$parts): void
{
    if (!is_array($node)) {
        return;
    }
    $type = (string)($node['type'] ?? '');
    if ($type === 'text') {
        $parts[] = (string)($node['text'] ?? '');
        return;
    }
    if ($type === 'mention') {
        $label = trim((string)($node['attrs']['label'] ?? ''));
        if ($label !== '') {
            $parts[] = (strpos($label, '@') === false ? '@' : '') . $label;
        }
        return;
    }
    if ($type === 'hardBreak') {
        $parts[] = ' ';
        return;
    }
    if (in_array($type, ['image', 'file', 'fileAttachment'], true)) {
        return;
    }
    if (isset($node['content']) && is_array($node['content'])) {
        foreach ($node['content'] as $child) {
            tm_report_collect_text($child, $parts);
        }
    }
    if (in_array($type, ['paragraph', 'heading', 'blockquote', 'listItem', 'bulletList', 'orderedList'], true)) {
        $parts[] = ' ';
    }
}

function tm_report_comment_text(array $comment): string
{
    $body = $comment['body'] ?? null;
    if (is_string($body)) {
        $decoded = json_decode($body, true);
        $body = is_array($decoded) ? $decoded : null;
    }
    if (!is_array($body)) {
        return '';
    }
    $parts = [];
    tm_report_collect_text($body, $parts);
    $text = preg_replace('/\s+/u', ' ', implode('', $parts));
    return tm_report_strip_file_names(trim((string)$text));
}

function tm_report_author_email(array $comment, array $people): string
{
    $author = is_array($comment['author'] ?? null) ? $comment['author'] : [];
    $email = trim((string)($author['email'] ?? ''));
    if ($email !== '') {
        return $email;
    }
    $name = trim((string)($author['name'] ?? ''));
    if ($name !== '' && isset($people[$name])) {
        return (string)$people[$name];
    }
    if (strpos($name, '@') !== false) {
        return $name;
    }
    return '';
}

function tm_report_latest_comment_timestamp(array $comments): string
{
    $latestIso = '';
    $latestTs = 0;
    foreach ($comments as $comment) {
        if (!is_array($comment)) {
            continue;
        }
        $createdAt = trim((string)($comment['createdAt'] ?? ''));
        if ($createdAt === '') {
            continue;
        }
        $createdTs = strtotime($createdAt);
        if ($createdTs === false || $createdTs < $latestTs) {
            continue;
        }
        $latestTs = $createdTs;
        $latestIso = $createdAt;
    }
    return $latestIso;
}

function tm_report_latest_comment_by_domain(array $comments, string $domain, array $people): string
{
    $needle = '@' . strtolower($domain);
    $latestText = '';
    $latestTs = 0;
    foreach ($comments as $comment) {
        if (!is_array($comment)) {
            continue;
        }
        $email = strtolower(tm_report_author_email($comment, $people));
        if ($email === '' || !str_ends_with($email, $needle)) {
            continue;
        }
        $createdAt = trim((string)($comment['createdAt'] ?? ''));
        $createdTs = $createdAt === '' ? 0 : (int)(strtotime($createdAt) ?: 0);
        if ($createdTs < $latestTs) {
            continue;
        }
        $text = tm_report_comment_text($comment);
        if ($text === '') {
            continue;
        }
        $latestTs = $createdTs;
        $latestText = $text;
    }
    return $latestText;
}

function reporting_build_rows_taskmanager(string $projectId, int $limit = 0): array
{
    $csv = tm_get_csv('/api/projects/' . rawurlencode($projectId) . '/export');
    $rows = tm_report_parse_csv($csv);
    $people = tm_people_map($rows);

    $tasks = [];
    foreach ($rows as $row) {
        if (trim((string)($row['Parent task'] ?? '')) !== '') {
            continue;
        }
        $taskId = trim((string)($row['Task ID'] ?? ''));
        $name = trim((string)($row['Name'] ?? ''));
        if ($taskId === '' || $name === '') {
            continue;
        }

        $detail = [];
        try {
            $detail = tm_get_json('/api/tasks/' . rawurlencode($taskId));
        } catch (TaskManagerAuthException $e) {
            throw $e;
        } catch (TaskManagerHttpException $e) {
            // Keep the ticket in the report even if its detail call fails.
            $detail = [];
        }

        $comments = is_array($detail['comments'] ?? null) ? $detail['comments'] : [];
        $created = trim((string)($detail['created']['at'] ?? ''));
        if ($created === '') {
            $created = trim((string)($row['Created At'] ?? ''));
        }
        $latestCommentAt = tm_report_latest_comment_timestamp($comments);

        $tasks[] = [
            'created_ts' => (int)(strtotime($created) ?: 0),
            'name' => $name,
            'row' => [
                '',
                tm_report_format_date($created),
                tm_report_format_date($latestCommentAt),
                tm_report_days_between($created, $latestCommentAt),
                $name,
                '',
                '',
                trim((string)($row['Platform'] ?? '')),
                trim((string)($row['Prority'] ?? '')),
                trim((string)($row['Section/Column'] ?? '')),
                tm_report_latest_comment_by_domain($comments, 'codigo.co', $people),
                tm_report_latest_comment_by_domain($comments, 'kmspks.org', $people),
                trim((string)($row['KMS'] ?? '')),
            ],
        ];

        if ($limit > 0 && count($tasks) >= $limit) {
            break;
        }
    }

    usort($tasks, static function (array $a, array $b): int {
        if ($a['created_ts'] !== $b['created_ts']) {
            return $a['created_ts'] <=> $b['created_ts'];
        }
        return strnatcasecmp($a['name'], $b['name']);
    });

    $result = [];
    $serial = 1;
    foreach ($tasks as $task) {
        $row = $task['row'];
        $row[0] = (string)$serial;
        $result[] = $row;
        $serial++;
    }
    return $result;
}

function reporting_generate_export_file_taskmanager(
    string $projectId,
    string $projectName,
    string $webRoot,
    string $exportsDir,
    string $downloadsFile,
    string $createdBy
): array {
    $headers = [
        'S/N',
        'Ticket Creation date',
        'Last Modified Date',
        'Days',
        'Issue Name & Title',
        'Module',
        'Department',
        'Platform',
        'Priority',
        'Status',
        'Last Comment from Codigo.co',
        'Last Comment from KMSPKS.org',
        'KMS-ID',
    ];

    $rows = reporting_build_rows_taskmanager($projectId);
    $xlsxPath = reporting_create_xlsx($headers, $rows, $webRoot . '/tmp');

    if (!is_dir($exportsDir)) {
        @mkdir($exportsDir, 0775, true);
    }
    $savedFileName = 'reporting-' . date('Ymd-His') . '-' . bin2hex(random_bytes(3)) . '.xlsx';
    $savedPath = $exportsDir . '/' . $savedFileName;
    if (!@rename($xlsxPath, $savedPath)) {
        if (!@copy($xlsxPath, $savedPath)) {
            throw new RuntimeException('Failed to save reporting file on server.');
        }
        @unlink($xlsxPath);
    }

    reporting_downloads_append($downloadsFile, [
        'file_name' => $savedFileName,
        'created_at' => gmdate('c'),
        'project_gid' => $projectId,
        'project_name' => $projectName,
        'row_count' => count($rows),
        'created_by' => $createdBy,
    ]);

    return [
        'file_name' => $savedFileName,
        'saved_path' => $savedPath,
        'row_count' => count($rows),
    ];
}
