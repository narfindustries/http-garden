<?php
    $encoded_headers = [];
    foreach (apache_request_headers() as $name => $value) {
        array_push($encoded_headers, [base64_encode($name), base64_encode($value)]);
    }

    $request = [
        'headers' => $encoded_headers,
        'body' => base64_encode(file_get_contents('php://input')),
        'method' => base64_encode($_SERVER['REQUEST_METHOD']),
        'uri' => base64_encode($_SERVER['REQUEST_URI']),
        'version' => base64_encode($_SERVER['SERVER_PROTOCOL'])
    ];

    echo json_encode($request);
?>
