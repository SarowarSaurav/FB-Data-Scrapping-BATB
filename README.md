if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST["username"];
    $password = $_POST["password"];
    $role = $_POST["role"];

    $sql = "SELECT * FROM users WHERE username = ? AND password = ? AND role = ?";
    $params = array($username, $password, $role);
    $query = sqlsrv_query($conn, $sql, $params);

    if ($row = sqlsrv_fetch_array($query)) {
        $_SESSION["username"] = $row["username"];
        $_SESSION["role"] = $row["role"];
        echo "1"; // Successful login
    } else {
        echo "2"; // Login failed
    }
}
