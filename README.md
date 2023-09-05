$sql = "SELECT * FROM your_table_name WHERE your_condition";

// Execute the query
$query = sqlsrv_query($conn, $sql);

if ($query === false) {
    die("Query execution failed: " . sqlsrv_errors());
}

// Fetch a single row
if ($row = sqlsrv_fetch_array($query, SQLSRV_FETCH_ASSOC)) {
    // Print the row data to the terminal
    print_r($row);
} else {
    echo "No data found for the given condition.";
}

// Close the connection
sqlsrv_close($conn);
