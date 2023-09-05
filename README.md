<?php
session_start();

$serverName = "your_server_name";
$connectionOptions = array(
    "Database" => "your_database_name",
    "Uid" => "your_username",
    "PWD" => "your_password"
);

$conn = sqlsrv_connect($serverName, $connectionOptions);

if (!$conn) {
    die("Connection failed: " . sqlsrv_errors());
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST["username"];
    $password = $_POST["password"];

    $sql = "SELECT * FROM users WHERE username = ? AND password = ?";
    $params = array($username, $password);
    $query = sqlsrv_query($conn, $sql, $params);

    if ($row = sqlsrv_fetch_array($query)) {
        $_SESSION["username"] = $row["username"];
        $_SESSION["role"] = $row["role"];
        echo "1"; // Successful login (return 1)
    } else {
        echo "2"; // Authentication failure (return 2)
    }
}

sqlsrv_close($conn);
?>
