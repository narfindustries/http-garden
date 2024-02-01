const port = 80;

const handler = async (request) => {
    let headers = [];
    for (const key of request.headers.keys()) {
        headers = headers.concat([
            [btoa(key), btoa(request.headers.get(key))]
        ]);
    }
    const url = new URL(request.url);
    let body;
    try {
        body = await request.arrayBuffer();
    }
    catch (_) {
        return new Response("Invalid message body", {status: 400});
    }
    return new Response(
        JSON.stringify({
            "headers": headers,
            "body": btoa(String.fromCharCode.apply(null, new Uint8Array(body))),
            "uri": btoa(url.pathname + url.search),
            "method": btoa(request.method),
            "version": ""
        }), {
            status: 200
        }
    );
};

Deno.serve({
    port
}, handler);
