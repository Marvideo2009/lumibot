<?php
header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

function loadEnv($path) {
    if (!file_exists($path)) return;
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (str_starts_with(trim($line), '#')) continue;
        [$name, $value] = explode("=", $line, 2);
        $name = trim($name);
        $value = trim($value);
        putenv("$name=$value");
    }
}

loadEnv(__DIR__ . '/.env');

$host = getenv("DB_HOST");
$db   = getenv("DB_NAME");
$user = getenv("DB_USER");
$pass = getenv("DB_PASS");

$options = [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
];

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $user, $pass, $options);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["error" => "DB connection failed"]);
    exit;
}

$action = $_GET["action"] ?? "";

if ($action === "add") {
    $userAgent = $_SERVER["HTTP_USER_AGENT"] ?? "";
    if (strpos($userAgent, "Lumibot/2.0") === false) {
        http_response_code(403);
        echo json_encode(["error" => "Forbidden"]);
        exit;
    }
    $data = json_decode(file_get_contents("php://input"), true);

    if (isset($data["url"])) {
        $data = [$data];
    }

    if (!is_array($data)) {
        http_response_code(400);
        echo json_encode(["error" => "Invalid JSON"]);
        exit;
    }

    $stmt = $pdo->prepare("INSERT INTO lumibot_pages (url, titre, description) VALUES (:url, :titre, :description)
                           ON DUPLICATE KEY UPDATE description=:description, titre=:titre, horodatage=NOW()");
    $inserted = 0;
    foreach ($data as $page) {
        if (!isset($page["url"]) || !isset($page["description"])) {
            continue;
        }
        $stmt->execute([
            ":url" => $page["url"],
            ":titre" => $page["titre"] ?? null,
            ":description" => $page["description"],
        ]);
        $inserted++;
    }

    echo json_encode(["status" => "ok", "inserted" => $inserted]);
} elseif ($action === "search") {
    $q = $_GET["q"] ?? "";
    if (!$q) {
        http_response_code(400);
        echo json_encode(["error" => "Missing query"]);
        exit;
    }

    $stmt = $pdo->prepare("SELECT url, titre, description FROM lumibot_pages 
                           WHERE MATCH(description, titre) AGAINST(:q IN NATURAL LANGUAGE MODE)
                           LIMIT 10");
    $stmt->execute([":q" => $q]);
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($results);
} elseif ($action === "export") {
    $sqlite = new SQLite3(":memory:");
    $sqlite->exec("CREATE TABLE pages (
        url TEXT PRIMARY KEY,
        titre TEXT,
        description TEXT
    )");

    $stmt = $pdo->query("SELECT url, titre, description FROM lumibot_pages");
    while ($row = $stmt->fetch()) {
        $url  = $sqlite->escapeString($row['url']);
        $titre = $sqlite->escapeString($row['titre']);
        $desc  = $sqlite->escapeString($row['description']);
        $sqlite->exec("INSERT OR REPLACE INTO pages (url, titre, description) 
                       VALUES ('$url', '$titre', '$desc')");
    }

    $tmpFile = tempnam(sys_get_temp_dir(), "lumibot_") . ".db";
    $backup = new SQLite3($tmpFile);
    $sqlite->backup($backup);
    $backup->close();
    $sqlite->close();

    header("Content-Type: application/octet-stream");
    header("Content-Disposition: attachment; filename=lumibot.db");
    header("Content-Length: " . filesize($tmpFile));
    readfile($tmpFile);

    unlink($tmpFile);
    exit;
} else {
    echo json_encode(["error" => "Unknown action"]);
}
