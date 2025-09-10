<?php
// api.php
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

// Config MySQL
$host = getenv("DB_HOST");
$db   = getenv("DB_NAME");
$user = getenv("DB_USER");
$pass = getenv("DB_PASS");

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["error" => "DB connection failed"]);
    exit;
}

// Récupérer action
$action = $_GET["action"] ?? "";

if ($action === "add") {
    $userAgent = $_SERVER["HTTP_USER_AGENT"] ?? "";
    if (strpos($userAgent, "Lumibot/2.0") === false) {
        http_response_code(403);
        echo json_encode(["error" => "Forbidden"]);
        exit;
    }
    // Ajouter une page (POST)
    $data = json_decode(file_get_contents("php://input"), true);

    if (!isset($data["url"]) || !isset($data["description"])) {
        http_response_code(400);
        echo json_encode(["error" => "Missing url or description"]);
        exit;
    }

    $stmt = $pdo->prepare("INSERT INTO pages (url, titre, description) VALUES (:url, :titre, :description)
                           ON DUPLICATE KEY UPDATE description=:description, titre=:titre, horodatage=NOW()");
    $stmt->execute([
        ":url" => $data["url"],
        ":titre" => $data["title"] ?? null,
        ":description" => $data["content"],
    ]);

    echo json_encode(["status" => "ok"]);
} elseif ($action === "search") {
    // Rechercher une page (GET)
    $q = $_GET["q"] ?? "";
    if (!$q) {
        http_response_code(400);
        echo json_encode(["error" => "Missing query"]);
        exit;
    }

    $stmt = $pdo->prepare("SELECT url, titre, description FROM pages 
                           WHERE MATCH(description, titre) AGAINST(:q IN NATURAL LANGUAGE MODE)
                           LIMIT 10");
    $stmt->execute([":q" => $q]);
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($results);
} else {
    echo json_encode(["error" => "Unknown action"]);
}