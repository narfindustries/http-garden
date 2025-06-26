Bun.serve({
    port: 80,
    async fetch(request) {
        let headers = [];
        for (const key of request.headers.keys()) {
            headers = headers.concat([
                [btoa(key), btoa(request.headers.get(key))]
            ]);
        }
        let url;
        try {
            url = new URL(request.url);
        }
        catch(_) {
            return new Response("Invalid URI", {status: 400});
        }
        return new Response(
            JSON.stringify({
                "headers": headers,
                "body": request.body ? Buffer.from(await Bun.readableStreamToArrayBuffer(request.body)).toString('base64') : "",
                "uri": btoa(url.pathname + url.search),
                "method": btoa(request.method),
                "version": ""
            }), {
                status: 200
            }
        );
    }
});
